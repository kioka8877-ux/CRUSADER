"""
crs_f03_gh_trigger.py — GitHub Actions Trigger pour F03 SIGISMUND
==================================================================
Orchestre le rendu Remotion distribué sur 10 workers GitHub Actions.

Fonctions exportées :
    upload_assets_to_release(f03_in, run_id, github_token, repo)
    trigger_workflow(run_id, fps, composition, total_frames, github_token, repo)
    poll_run_status(gh_run_id, github_token, repo, timeout_min=90)
    download_final_artifact(gh_run_id, run_id, github_token, repo, output_dir)
    audit_run(gh_run_id, github_token, repo)         ← NOUVEAU : poste de contrôle
    preflight_result(gh_run_id, github_token, repo)  ← NOUVEAU : lire verdict Go/No-Go

Usage depuis CRS_F03.ipynb Étapes 7, 8a, 8b, 8c, 9.
"""

import os
import time
import json
import zipfile
import requests
import tempfile

GH_API        = "https://api.github.com"
WORKFLOW_FILE = "f03_render.yml"
N_WORKERS     = 10


# ─── Helpers internes ─────────────────────────────────────────────────────────

def _headers(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _check(resp, label=""):
    if not resp.ok:
        raise RuntimeError(
            f"[GitHub API] {label} — {resp.status_code}\n{resp.text[:800]}"
        )
    return resp


# ─── 1. Upload des assets vers une GitHub Release temporaire ─────────────────

def upload_assets_to_release(f03_in: str, run_id: str, github_token: str, repo: str) -> str:
    """
    Crée une GitHub Release temporaire taguée run_id et upload les assets F03.
    Retourne l'URL de la release créée.

    Assets uploadés :
        timing.json, roadmap.json, audio_clean.mp3, images.zip
    """
    h = _headers(github_token)

    # Supprimer release précédente si elle existe (tag identique)
    r = requests.get(f"{GH_API}/repos/{repo}/releases/tags/{run_id}", headers=h)
    if r.ok:
        release_id = r.json()["id"]
        requests.delete(f"{GH_API}/repos/{repo}/releases/{release_id}", headers=h)
        requests.delete(f"{GH_API}/repos/{repo}/git/refs/tags/{run_id}", headers=h)
        print(f"[UPLOAD] Release précédente {run_id} supprimée.")

    # Créer la release
    payload = {
        "tag_name": run_id,
        "name": f"[TEMP] F03 Assets — {run_id}",
        "body": "Release temporaire générée par crs_f03_gh_trigger.py. Ne pas supprimer manuellement pendant le rendu.",
        "draft": False,
        "prerelease": True,
    }
    r = _check(
        requests.post(f"{GH_API}/repos/{repo}/releases", headers=h, json=payload),
        "create release",
    )
    release      = r.json()
    upload_url   = release["upload_url"].split("{")[0]
    release_url  = release["html_url"]
    print(f"[UPLOAD] Release créée : {release_url}")

    # Upload fichiers plats
    for fname in ["timing.json", "roadmap.json", "audio_clean.mp3"]:
        fpath = os.path.join(f03_in, fname)
        if not os.path.isfile(fpath):
            print(f"[UPLOAD] {fname} absent — ignoré.")
            continue
        with open(fpath, "rb") as f:
            data = f.read()
        ct = "application/json" if fname.endswith(".json") else "audio/mpeg"
        _check(
            requests.post(
                f"{upload_url}?name={fname}",
                headers={**h, "Content-Type": ct},
                data=data,
            ),
            f"upload {fname}",
        )
        print(f"[UPLOAD] {fname} — {len(data) / 1024:.1f} KB")

    # Zipper et uploader images/
    images_dir = os.path.join(f03_in, "images")
    if os.path.isdir(images_dir):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = tmp.name
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for img_name in sorted(os.listdir(images_dir)):
                img_path = os.path.join(images_dir, img_name)
                if os.path.isfile(img_path):
                    zf.write(img_path, os.path.join("images", img_name))
        zip_size = os.path.getsize(zip_path)
        with open(zip_path, "rb") as f:
            data = f.read()
        _check(
            requests.post(
                f"{upload_url}?name=images.zip",
                headers={**h, "Content-Type": "application/zip"},
                data=data,
            ),
            "upload images.zip",
        )
        os.unlink(zip_path)
        print(f"[UPLOAD] images.zip — {zip_size / 1024 / 1024:.1f} MB")
    else:
        print("[UPLOAD] Aucun dossier images/ — continue sans images.")

    print(f"[UPLOAD] Assets disponibles sur la Release {run_id}.")
    return release_url


# ─── 2. Déclenchement du workflow GitHub Actions ──────────────────────────────

def trigger_workflow(
    run_id: str,
    fps: int,
    composition: str,
    total_frames: int,
    github_token: str,
    repo: str,
) -> int:
    """
    Déclenche le workflow f03_render.yml via workflow_dispatch.
    Retourne l'ID du GitHub Actions run créé.
    """
    h = _headers(github_token)

    payload = {
        "ref": "main",
        "inputs": {
            "run_id":       run_id,
            "fps":          str(fps),
            "composition":  composition,
            "total_frames": str(total_frames),
        },
    }
    _check(
        requests.post(
            f"{GH_API}/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/dispatches",
            headers=h,
            json=payload,
        ),
        "workflow dispatch",
    )
    print(f"[DISPATCH] Workflow déclenché — run_id={run_id}, total_frames={total_frames}")

    # Trouver l'ID du run créé (attendre que GitHub l'enregistre)
    time.sleep(6)
    for attempt in range(12):
        r = requests.get(
            f"{GH_API}/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/runs",
            headers=h,
            params={"per_page": 5},
        )
        if r.ok:
            runs = r.json().get("workflow_runs", [])
            if runs:
                gh_run_id = runs[0]["id"]
                print(f"[DISPATCH] GitHub Actions run ID : {gh_run_id}")
                return gh_run_id
        time.sleep(4)

    raise RuntimeError(
        "[DISPATCH] Impossible de récupérer le run ID.\n"
        f"Vérifiez manuellement : https://github.com/{repo}/actions"
    )


# ─── 3. Polling du statut du run ─────────────────────────────────────────────

def poll_run_status(
    gh_run_id: int,
    github_token: str,
    repo: str,
    timeout_min: int = 90,
) -> str:
    """
    Poll le run GitHub Actions jusqu'à complétion.
    Affiche la progression toutes les 15 secondes.
    Retourne 'success' ou lève RuntimeError si échec/timeout.
    """
    h        = _headers(github_token)
    url      = f"{GH_API}/repos/{repo}/actions/runs/{gh_run_id}"
    jobs_url = f"{GH_API}/repos/{repo}/actions/runs/{gh_run_id}/jobs"
    deadline = time.time() + timeout_min * 60

    print(f"[POLL] Surveillance du run {gh_run_id}...")
    print(f"[POLL] Timeout : {timeout_min} min")
    print(f"[POLL] Suivi : https://github.com/{repo}/actions/runs/{gh_run_id}\n")

    while time.time() < deadline:
        r = requests.get(url, headers=h)
        if not r.ok:
            print(f"[POLL] API error {r.status_code} — retry dans 15s...")
            time.sleep(15)
            continue

        run        = r.json()
        status     = run["status"]
        conclusion = run.get("conclusion")

        # Compter les jobs terminés
        rj = requests.get(jobs_url, headers=h)
        completed_jobs = 0
        total_jobs     = 0
        if rj.ok:
            jobs           = rj.json().get("jobs", [])
            total_jobs     = len(jobs)
            completed_jobs = sum(1 for j in jobs if j["status"] == "completed")

        print(
            f"  {time.strftime('%H:%M:%S')} | Status : {status:<12} | "
            f"Jobs terminés : {completed_jobs}/{total_jobs}"
        )

        if status == "completed":
            if conclusion == "success":
                print(f"\n[POLL] Run {gh_run_id} terminé avec succès.")
                return "success"
            else:
                raise RuntimeError(
                    f"[POLL] Run {gh_run_id} terminé avec conclusion : {conclusion}\n"
                    f"Détails : https://github.com/{repo}/actions/runs/{gh_run_id}"
                )

        time.sleep(15)

    raise RuntimeError(f"[POLL] Timeout après {timeout_min} min — run toujours en cours.")


# ─── 4. Téléchargement de l'artifact final + nettoyage release ───────────────

def download_final_artifact(
    gh_run_id: int,
    run_id: str,
    github_token: str,
    repo: str,
    output_dir: str,
) -> str:
    """
    Télécharge l'artifact 'resultat-final' depuis le run GitHub Actions.
    Extrait short_render.mp4 dans output_dir.
    Supprime la GitHub Release temporaire run_id après téléchargement.
    Retourne le chemin local du .mp4.
    """
    h = _headers(github_token)

    # Lister les artifacts du run
    r = _check(
        requests.get(
            f"{GH_API}/repos/{repo}/actions/runs/{gh_run_id}/artifacts",
            headers=h,
        ),
        "list artifacts",
    )
    artifacts = r.json().get("artifacts", [])
    final = next((a for a in artifacts if a["name"] == "resultat-final"), None)
    if not final:
        raise RuntimeError(
            "[DOWNLOAD] Artifact 'resultat-final' introuvable.\n"
            f"Artifacts disponibles : {[a['name'] for a in artifacts]}"
        )

    artifact_id = final["id"]
    size_mb     = final["size_in_bytes"] / 1024 / 1024
    print(f"[DOWNLOAD] Artifact trouvé : ID={artifact_id}, taille={size_mb:.1f} MB")

    # Télécharger le zip de l'artifact
    r = requests.get(
        f"{GH_API}/repos/{repo}/actions/artifacts/{artifact_id}/zip",
        headers=h,
        allow_redirects=True,
    )
    _check(r, "download artifact zip")

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(r.content)
        zip_path = tmp.name

    # Extraire short_render.mp4
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "short_render.mp4")
    with zipfile.ZipFile(zip_path, "r") as zf:
        mp4_names = [n for n in zf.namelist() if n.endswith(".mp4")]
        if not mp4_names:
            raise RuntimeError("[DOWNLOAD] Aucun .mp4 trouvé dans l'artifact zip.")
        with zf.open(mp4_names[0]) as src, open(output_path, "wb") as dst:
            dst.write(src.read())

    os.unlink(zip_path)
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[DOWNLOAD] short_render.mp4 sauvegardé : {output_path} ({size_mb:.1f} MB)")

    # Nettoyage : supprimer la release temporaire
    try:
        r = requests.get(f"{GH_API}/repos/{repo}/releases/tags/{run_id}", headers=h)
        if r.ok:
            release_id = r.json()["id"]
            requests.delete(f"{GH_API}/repos/{repo}/releases/{release_id}", headers=h)
            requests.delete(f"{GH_API}/repos/{repo}/git/refs/tags/{run_id}", headers=h)
            print(f"[CLEANUP] Release temporaire {run_id} supprimée.")
    except Exception as e:
        print(f"[CLEANUP] Nettoyage release échoué (non bloquant) : {e}")

    return output_path


# ─── 5. AUDIT RUN — Poste de contrôle sophistiqué ────────────────────────────

def audit_run(gh_run_id: int, github_token: str, repo: str) -> dict:
    """
    Rapport complet sur l'état d'un run en cours ou terminé.

    Retourne un dict avec :
        status          : 'running' | 'success' | 'failed' | 'cancelled'
        preflight       : dict  (go/no-go, durée, taille preflight.mp4)
        chunks          : list  (état de chaque chunk 0-9)
        concat          : dict  (état du job concat)
        freeze_detected : bool  (True si un job est bloqué sans progress)
        verdict         : str   (résumé humain)
        url             : str   (lien GitHub Actions)

    Usage depuis Colab : rapport = audit_run(gh_run_id, token, repo)
    """
    h = _headers(github_token)

    run_url  = f"{GH_API}/repos/{repo}/actions/runs/{gh_run_id}"
    jobs_url = f"{GH_API}/repos/{repo}/actions/runs/{gh_run_id}/jobs?per_page=50"

    # Infos du run global
    r_run = requests.get(run_url, headers=h)
    if not r_run.ok:
        return {"status": "error", "verdict": f"API error {r_run.status_code}"}

    run        = r_run.json()
    run_status = run["status"]
    run_concl  = run.get("conclusion") or "—"
    run_start  = run.get("created_at", "?")

    # Liste des jobs
    r_jobs = requests.get(jobs_url, headers=h)
    jobs   = r_jobs.json().get("jobs", []) if r_jobs.ok else []

    now = time.time()

    # ── Classer les jobs ──────────────────────────────────────────────────────
    preflight_job = None
    chunk_jobs    = {}   # {chunk_num: job}
    concat_job    = None

    for job in jobs:
        name = job["name"]
        if "Preflight" in name:
            preflight_job = job
        elif "Chunk" in name:
            try:
                num = int(name.split("Chunk")[1].strip().split()[0])
                chunk_jobs[num] = job
            except (ValueError, IndexError):
                pass
        elif "Concat" in name:
            concat_job = job

    # ── Analyser chaque chunk ─────────────────────────────────────────────────
    def _job_summary(job):
        if job is None:
            return {"status": "not_started"}

        status    = job["status"]
        concl     = job.get("conclusion") or "—"
        started   = job.get("started_at")
        completed = job.get("completed_at")

        elapsed = "?"
        if started:
            import datetime
            start_dt = datetime.datetime.fromisoformat(started.replace("Z", "+00:00"))
            if completed:
                end_dt  = datetime.datetime.fromisoformat(completed.replace("Z", "+00:00"))
                elapsed = f"{int((end_dt - start_dt).total_seconds())}s"
            else:
                elapsed = f"{int(time.time() - start_dt.timestamp())}s (en cours)"

        return {
            "status":   status,
            "conclusion": concl,
            "elapsed":  elapsed,
            "job_id":   job["id"],
            "html_url": job["html_url"],
        }

    # ── Détecter les freezes ──────────────────────────────────────────────────
    # Un job est suspect si : status=in_progress ET démarré depuis > FREEZE_THRESHOLD_MIN
    FREEZE_THRESHOLD_MIN = 8
    freeze_detected = False
    freeze_jobs     = []

    for job in jobs:
        if job["status"] == "in_progress" and job.get("started_at"):
            import datetime
            start_dt = datetime.datetime.fromisoformat(job["started_at"].replace("Z", "+00:00"))
            elapsed_min = (time.time() - start_dt.timestamp()) / 60
            if elapsed_min > FREEZE_THRESHOLD_MIN:
                freeze_detected = True
                freeze_jobs.append(f"{job['name']} ({elapsed_min:.1f} min)")

    # ── Lire les logs du dernier job en freeze (pour diagnostic) ─────────────
    freeze_log_snippet = None
    if freeze_detected and freeze_jobs:
        # Prendre le job le plus suspect (le premier chunk en freeze)
        for job in jobs:
            if job["status"] == "in_progress" and "Chunk" in job["name"]:
                log_url  = f"{GH_API}/repos/{repo}/actions/jobs/{job['id']}/logs"
                r_log    = requests.get(log_url, headers=h, allow_redirects=True)
                if r_log.ok:
                    lines = r_log.text.strip().split("\n")
                    # Garder les 10 dernières lignes utiles (non vides)
                    tail = [l for l in lines if l.strip()][-10:]
                    freeze_log_snippet = "\n".join(tail)
                break

    # ── Construire le rapport ─────────────────────────────────────────────────
    chunks_summary = {i: _job_summary(chunk_jobs.get(i)) for i in range(10)}

    done    = sum(1 for s in chunks_summary.values() if s["status"] == "completed" and s["conclusion"] == "success")
    failed  = sum(1 for s in chunks_summary.values() if s["conclusion"] == "failure")
    running = sum(1 for s in chunks_summary.values() if s["status"] == "in_progress")
    waiting = sum(1 for s in chunks_summary.values() if s["status"] == "queued")

    # Verdict humain
    if run_status == "completed" and run_concl == "success":
        verdict = f"✅ RUN TERMINÉ AVEC SUCCÈS — {done}/10 chunks OK"
    elif run_status == "completed":
        verdict = f"❌ RUN TERMINÉ EN ÉCHEC — conclusion={run_concl}"
    elif freeze_detected:
        verdict = f"⚠️  FREEZE DÉTECTÉ — {', '.join(freeze_jobs)}"
    elif failed > 0:
        verdict = f"❌ {failed} chunk(s) en échec sur {10}"
    else:
        verdict = (
            f"⏳ EN COURS — {done} OK / {running} actifs / {waiting} en attente / {failed} échecs"
        )

    report = {
        "status":          run_status,
        "conclusion":      run_concl,
        "run_start":       run_start,
        "preflight":       _job_summary(preflight_job),
        "chunks":          chunks_summary,
        "concat":          _job_summary(concat_job),
        "freeze_detected": freeze_detected,
        "freeze_jobs":     freeze_jobs,
        "freeze_log":      freeze_log_snippet,
        "verdict":         verdict,
        "url":             f"https://github.com/{repo}/actions/runs/{gh_run_id}",
    }

    # ── Affichage console structuré ───────────────────────────────────────────
    print("\n" + "═" * 60)
    print(f"  AUDIT RUN {gh_run_id}")
    print(f"  {verdict}")
    print("═" * 60)
    print(f"  Preflight : {_job_summary(preflight_job)['status']} / {_job_summary(preflight_job)['conclusion']} ({_job_summary(preflight_job)['elapsed']})")
    print(f"  Chunks :")
    for i in range(10):
        s = chunks_summary[i]
        icon = {"success": "✅", "failure": "❌", "in_progress": "⏳", "queued": "⌛"}.get(
            s.get("conclusion") or s["status"], "—"
        )
        print(f"    {icon}  Chunk {i:2d} : {s['status']:<12} {s['conclusion']:<10} {s['elapsed']}")
    print(f"  Concat   : {_job_summary(concat_job)['status']} / {_job_summary(concat_job)['conclusion']} ({_job_summary(concat_job)['elapsed']})")

    if freeze_detected:
        print(f"\n  ⚠️  FREEZE — Jobs suspects : {', '.join(freeze_jobs)}")
        if freeze_log_snippet:
            print(f"\n  Dernières lignes de log :\n{'─'*40}")
            for line in freeze_log_snippet.split("\n"):
                print(f"    {line}")
            print("─" * 40)

    print(f"\n  Lien : {report['url']}")
    print("═" * 60 + "\n")

    return report


# ─── 6. Résultat Preflight — lecture rapide Go/No-Go ─────────────────────────

def preflight_result(gh_run_id: int, github_token: str, repo: str) -> dict:
    """
    Lit uniquement le résultat du job Preflight d'un run.
    Plus rapide qu'audit_run() — utile après l'étape 8b pour savoir si
    le preflight a passé avant que les 10 chunks démarrent.

    Retourne : {'go': bool, 'status': str, 'elapsed': str, 'conclusion': str}
    """
    h = _headers(github_token)
    jobs_url = f"{GH_API}/repos/{repo}/actions/runs/{gh_run_id}/jobs?per_page=20"

    r = requests.get(jobs_url, headers=h)
    if not r.ok:
        return {"go": False, "status": "error", "elapsed": "?", "conclusion": "api_error"}

    jobs = r.json().get("jobs", [])
    preflight = next((j for j in jobs if "Preflight" in j["name"]), None)

    if preflight is None:
        return {"go": False, "status": "not_found", "elapsed": "?", "conclusion": "?"}

    status = preflight["status"]
    concl  = preflight.get("conclusion") or "pending"

    elapsed = "?"
    if preflight.get("started_at"):
        import datetime
        start_dt = datetime.datetime.fromisoformat(preflight["started_at"].replace("Z", "+00:00"))
        if preflight.get("completed_at"):
            end_dt  = datetime.datetime.fromisoformat(preflight["completed_at"].replace("Z", "+00:00"))
            elapsed = f"{int((end_dt - start_dt).total_seconds())}s"
        else:
            elapsed = f"{int(time.time() - start_dt.timestamp())}s"

    go = (status == "completed" and concl == "success")

    icon = "✅ GO" if go else ("⏳ EN COURS" if status == "in_progress" else f"❌ NO-GO ({concl})")
    print(f"[PREFLIGHT] {icon} — {elapsed}")

    return {"go": go, "status": status, "elapsed": elapsed, "conclusion": concl}
