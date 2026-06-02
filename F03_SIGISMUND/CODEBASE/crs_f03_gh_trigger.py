"""
crs_f03_gh_trigger.py — GitHub Actions Trigger pour F03 SIGISMUND
==================================================================
Remplace crs_f03_modal_worker.py.

Orchestre le rendu Remotion distribue sur 10 workers GitHub Actions.

Fonctions exportees :
    upload_assets_to_release(f03_in, run_id, github_token, repo)
    trigger_workflow(run_id, fps, composition, total_frames, github_token, repo)
    poll_run_status(gh_run_id, github_token, repo, timeout_min=90)
    download_final_artifact(gh_run_id, run_id, github_token, repo, output_dir)

Usage depuis CRS_F03.ipynb Etapes 7, 8b, 8c, 9.
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
    Cree une GitHub Release temporaire tagguee run_id et upload les assets F03.
    Retourne l'URL de la release creee.

    Assets uploades :
        timing.json, roadmap.json, audio_clean.mp3, images.zip
    """
    h = _headers(github_token)

    # ── Supprimer release precedente si elle existe (tag identique) ──────────
    r = requests.get(f"{GH_API}/repos/{repo}/releases/tags/{run_id}", headers=h)
    if r.ok:
        release_id = r.json()["id"]
        requests.delete(f"{GH_API}/repos/{repo}/releases/{release_id}", headers=h)
        requests.delete(f"{GH_API}/repos/{repo}/git/refs/tags/{run_id}", headers=h)
        print(f"[UPLOAD] Release precedente {run_id} supprimee.")

    # ── Creer la release ──────────────────────────────────────────────────────
    payload = {
        "tag_name": run_id,
        "name": f"[TEMP] F03 Assets — {run_id}",
        "body": "Release temporaire generee par crs_f03_gh_trigger.py. Ne pas supprimer manuellement pendant le rendu.",
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
    print(f"[UPLOAD] Release creee : {release_url}")

    # ── Upload fichiers plats ─────────────────────────────────────────────────
    for fname in ["timing.json", "roadmap.json", "audio_clean.mp3"]:
        fpath = os.path.join(f03_in, fname)
        if not os.path.isfile(fpath):
            print(f"[UPLOAD] {fname} absent — ignore.")
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

    # ── Zipper et uploader images/ ────────────────────────────────────────────
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


# ─── 2. Declenchement du workflow GitHub Actions ──────────────────────────────

def trigger_workflow(
    run_id: str,
    fps: int,
    composition: str,
    total_frames: int,
    github_token: str,
    repo: str,
) -> int:
    """
    Declenche le workflow f03_render.yml via workflow_dispatch.
    Retourne l'ID du GitHub Actions run cree.
    """
    h = _headers(github_token)

    payload = {
        "ref": "main",
        "inputs": {
            "run_id":        run_id,
            "fps":           str(fps),
            "composition":   composition,
            "total_frames":  str(total_frames),
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
    print(f"[DISPATCH] Workflow declenche — run_id={run_id}, total_frames={total_frames}")

    # ── Trouver l'ID du run cree (attendre que GitHub l'enregistre) ───────────
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
        "[DISPATCH] Impossible de recuperer le run ID.\n"
        f"Verifiez manuellement : https://github.com/{repo}/actions"
    )


# ─── 3. Polling du statut du run ─────────────────────────────────────────────

def poll_run_status(
    gh_run_id: int,
    github_token: str,
    repo: str,
    timeout_min: int = 90,
) -> str:
    """
    Poll le run GitHub Actions jusqu'a completion.
    Affiche la progression toutes les 15 secondes.
    Retourne 'success' ou leve RuntimeError si echec/timeout.
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

        # Compter les jobs termines
        rj = requests.get(jobs_url, headers=h)
        completed_jobs = 0
        total_jobs     = 0
        if rj.ok:
            jobs           = rj.json().get("jobs", [])
            total_jobs     = len(jobs)
            completed_jobs = sum(1 for j in jobs if j["status"] == "completed")

        print(
            f"  {time.strftime('%H:%M:%S')} | Status : {status:<12} | "
            f"Jobs termines : {completed_jobs}/{total_jobs}"
        )

        if status == "completed":
            if conclusion == "success":
                print(f"\n[POLL] Run {gh_run_id} termine avec succes.")
                return "success"
            else:
                raise RuntimeError(
                    f"[POLL] Run {gh_run_id} termine avec conclusion : {conclusion}\n"
                    f"Details : https://github.com/{repo}/actions/runs/{gh_run_id}"
                )

        time.sleep(15)

    raise RuntimeError(f"[POLL] Timeout apres {timeout_min} min — run toujours en cours.")


# ─── 4. Telechargement de l'artifact final + nettoyage release ───────────────

def download_final_artifact(
    gh_run_id: int,
    run_id: str,
    github_token: str,
    repo: str,
    output_dir: str,
) -> str:
    """
    Telecharge l'artifact 'resultat-final' depuis le run GitHub Actions.
    Extrait short_render.mp4 dans output_dir.
    Supprime la GitHub Release temporaire run_id apres telechargement.
    Retourne le chemin local du .mp4.
    """
    h = _headers(github_token)

    # ── Lister les artifacts du run ───────────────────────────────────────────
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
    print(f"[DOWNLOAD] Artifact trouve : ID={artifact_id}, taille={size_mb:.1f} MB")

    # ── Telecharger le zip de l'artifact ─────────────────────────────────────
    r = requests.get(
        f"{GH_API}/repos/{repo}/actions/artifacts/{artifact_id}/zip",
        headers=h,
        allow_redirects=True,
    )
    _check(r, "download artifact zip")

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(r.content)
        zip_path = tmp.name

    # ── Extraire short_render.mp4 ─────────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "short_render.mp4")
    with zipfile.ZipFile(zip_path, "r") as zf:
        mp4_names = [n for n in zf.namelist() if n.endswith(".mp4")]
        if not mp4_names:
            raise RuntimeError("[DOWNLOAD] Aucun .mp4 trouve dans l'artifact zip.")
        with zf.open(mp4_names[0]) as src, open(output_path, "wb") as dst:
            dst.write(src.read())

    os.unlink(zip_path)
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[DOWNLOAD] short_render.mp4 sauvegarde : {output_path} ({size_mb:.1f} MB)")

    # ── Nettoyage : supprimer la release temporaire ───────────────────────────
    try:
        r = requests.get(f"{GH_API}/repos/{repo}/releases/tags/{run_id}", headers=h)
        if r.ok:
            release_id = r.json()["id"]
            requests.delete(f"{GH_API}/repos/{repo}/releases/{release_id}", headers=h)
            requests.delete(f"{GH_API}/repos/{repo}/git/refs/tags/{run_id}", headers=h)
            print(f"[CLEANUP] Release temporaire {run_id} supprimee.")
    except Exception as e:
        print(f"[CLEANUP] Nettoyage release echoue (non bloquant) : {e}")

    return output_path
