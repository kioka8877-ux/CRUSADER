"""
CRS_EXECUTEUR.py — Orchestrateur CRUSADER v2 (GitHub Actions Edition)
======================================================================
Sandbox = télécommande uniquement.
Toutes les frégates tournent sur GitHub Actions.
L'opérateur intervient aux 4 gates.

Usage:
    python CRS_EXECUTEUR.py --start --title "Mon sujet"
    python CRS_EXECUTEUR.py --gate G2    # Télécharge F01, lance viewer F02
    python CRS_EXECUTEUR.py --gate G3    # Trigger F03 sur GH
    python CRS_EXECUTEUR.py --gate G4    # Télécharge F03, trigger F04 sur GH
    python CRS_EXECUTEUR.py --close      # Télécharge artefact final F04
    python CRS_EXECUTEUR.py --resume     # Reprendre depuis ledger

Variables d'environnement requises:
    GH_TOKEN — token GitHub (scope: repo)
"""

import argparse
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

# ─── Dépendance requests (auto-install si absente) ────────────────────────────
try:
    import requests
except ImportError:
    print("[SETUP] Installation de requests...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "requests",
        "--quiet", "--break-system-packages"
    ])
    import requests

# ─── Chemins ──────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.resolve()
LEDGER_FILE = REPO_ROOT / "crs_ledger.json"
SHARED_IN   = REPO_ROOT / "SHARED" / "IN"
F01_OUT     = REPO_ROOT / "F01_GRIMALDUS" / "F01B_GRIMALDUS" / "OUT"
F02_IN      = REPO_ROOT / "F02_CASTELLAN" / "IN"
F02_OUT     = REPO_ROOT / "F02_CASTELLAN" / "OUT"
F03_OUT     = REPO_ROOT / "F03_SIGISMUND" / "OUT"
F04_OUT     = REPO_ROOT / "F04_HELBRECHT" / "OUT"

GH_API = "https://api.github.com"

# ─── Ledger ───────────────────────────────────────────────────────────────────

def load_ledger():
    with open(LEDGER_FILE) as f:
        return json.load(f)

def save_ledger(ledger):
    ledger["derniere_mise_a_jour"] = datetime.datetime.now().isoformat()
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)

# ─── GitHub API helpers ───────────────────────────────────────────────────────

def _h(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def _check(resp, label=""):
    if not resp.ok:
        raise RuntimeError(f"[GH API] {label} — {resp.status_code}\n{resp.text[:500]}")
    return resp

def create_or_reset_release(tag, name, token, repo):
    h = _h(token)
    r = requests.get(f"{GH_API}/repos/{repo}/releases/tags/{tag}", headers=h)
    if r.ok:
        rid = r.json()["id"]
        requests.delete(f"{GH_API}/repos/{repo}/releases/{rid}", headers=h)
        requests.delete(f"{GH_API}/repos/{repo}/git/refs/tags/{tag}", headers=h)
        print(f"[RELEASE] Release précédente {tag} supprimée.")
    r = _check(
        requests.post(f"{GH_API}/repos/{repo}/releases", headers=h, json={
            "tag_name": tag, "name": name, "draft": False, "prerelease": True,
        }),
        "create release"
    )
    rel = r.json()
    print(f"[RELEASE] Créée : {rel['html_url']}")
    return rel

def upload_asset(upload_url_base, fname, fpath, content_type, token):
    with open(fpath, "rb") as f:
        data = f.read()
    _check(
        requests.post(
            f"{upload_url_base}?name={fname}",
            headers={**_h(token), "Content-Type": content_type},
            data=data,
        ),
        f"upload {fname}",
    )
    print(f"[UPLOAD] {fname} — {len(data)/1024:.1f} KB ✅")

def upload_asset_bytes(upload_url_base, fname, data, content_type, token):
    _check(
        requests.post(
            f"{upload_url_base}?name={fname}",
            headers={**_h(token), "Content-Type": content_type},
            data=data,
        ),
        f"upload {fname}",
    )
    print(f"[UPLOAD] {fname} — {len(data)/1024:.1f} KB ✅")

def trigger_workflow_and_get_url(workflow_file, inputs, token, repo):
    h = _h(token)
    _check(
        requests.post(
            f"{GH_API}/repos/{repo}/actions/workflows/{workflow_file}/dispatches",
            headers=h,
            json={"ref": "main", "inputs": inputs},
        ),
        "workflow dispatch",
    )
    time.sleep(5)
    r = requests.get(
        f"{GH_API}/repos/{repo}/actions/workflows/{workflow_file}/runs",
        headers=h,
        params={"per_page": 1},
    )
    if r.ok:
        runs = r.json().get("workflow_runs", [])
        if runs:
            gh_run_id = runs[0]["id"]
            url       = runs[0]["html_url"]
            print(f"[DISPATCH] Run ID : {gh_run_id}")
            return gh_run_id, url
    return None, f"https://github.com/{repo}/actions"

def download_artifact_to(gh_run_id, artifact_name, dest_dir, token, repo):
    h = _h(token)
    r = _check(
        requests.get(f"{GH_API}/repos/{repo}/actions/runs/{gh_run_id}/artifacts", headers=h),
        "list artifacts",
    )
    arts = r.json().get("artifacts", [])
    art  = next((a for a in arts if a["name"] == artifact_name), None)
    if not art:
        names = [a["name"] for a in arts]
        raise RuntimeError(f"[DOWNLOAD] Artifact '{artifact_name}' introuvable. Disponibles: {names}")
    r = requests.get(
        f"{GH_API}/repos/{repo}/actions/artifacts/{art['id']}/zip",
        headers=h, allow_redirects=True,
    )
    _check(r, "download artifact zip")
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall(dest)
    print(f"[DOWNLOAD] {artifact_name} → {dest}")

def zip_images(images_dir):
    buf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for img in sorted(Path(images_dir).iterdir()):
            if img.is_file():
                zf.write(img, f"images/{img.name}")
                count += 1
    buf.seek(0)
    return buf.read(), count

# ─── START ────────────────────────────────────────────────────────────────────

def cmd_start(title, token, ledger):
    print("\n═══════════════════════════════════════════")
    print("  CRUSADER — START")
    print("═══════════════════════════════════════════\n")

    repo   = ledger["github_repo"]
    ts     = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    run_id = f"CRS_{ts}"

    audio  = SHARED_IN / "audio_raw.mp3"
    images = SHARED_IN / "images"
    if not audio.exists():
        print(f"[START] ERREUR : audio_raw.mp3 absent dans {SHARED_IN}")
        sys.exit(1)
    if not images.exists() or not any(images.iterdir()):
        print(f"[START] ERREUR : images/ absent ou vide dans {SHARED_IN}")
        sys.exit(1)

    release    = create_or_reset_release(run_id, f"[CRUSADER] {run_id} — {title}", token, repo)
    upload_url = release["upload_url"].split("{")[0]

    upload_asset(upload_url, "audio_raw.mp3", audio, "audio/mpeg", token)

    zip_data, img_count = zip_images(images)
    upload_asset_bytes(upload_url, "images.zip", zip_data, "application/zip", token)
    print(f"[UPLOAD] images.zip ({img_count} images) ✅")

    gh_run_id, url = trigger_workflow_and_get_url(
        "f01_grimaldus.yml", {"run_id": run_id}, token, repo
    )

    ledger.update({
        "run_id":            run_id,
        "production_title":  title,
        "gate_actuelle":     "G2",
        "etapes_completees": ["F01_triggered"],
        "gh_runs":           {"f01": gh_run_id},
        "repo_root":         str(REPO_ROOT),
    })
    save_ledger(ledger)

    print("\n════════════════════════════════════════════")
    print("  GATE 1 — F01 EN COURS SUR GITHUB ACTIONS")
    print(f"  Surveille : {url}")
    print("  Quand F01 terminé → python CRS_EXECUTEUR.py --gate G2")
    print("════════════════════════════════════════════\n")

# ─── GATE G2 : Viewer F02 ─────────────────────────────────────────────────────

def cmd_gate_g2(token, ledger):
    print("\n═══════════════════════════════════════════")
    print("  CRUSADER — GATE G2 (F02 Viewer)")
    print("═══════════════════════════════════════════\n")

    repo          = ledger["github_repo"]
    gh_run_id_f01 = ledger.get("gh_runs", {}).get("f01")
    if not gh_run_id_f01:
        print("[G2] ERREUR : run ID F01 absent du ledger. Relancez --start.")
        sys.exit(1)

    # Télécharger artefacts F01
    F01_OUT.mkdir(parents=True, exist_ok=True)
    print("[G2] Téléchargement artefacts F01...")
    download_artifact_to(gh_run_id_f01, "f01-output", F01_OUT, token, repo)

    timing_path = F01_OUT / "timing.json"
    if not timing_path.exists():
        print(f"[G2] ERREUR : timing.json absent dans {F01_OUT}")
        sys.exit(1)

    with open(timing_path) as f:
        timing = json.load(f)
    meta = timing.get("meta", {})
    print(f"[G2] timing.json OK — {meta.get('total_frames', '?')} frames, {meta.get('duration_seconds', '?')}s")

    # Préparer F02/IN
    F02_IN.mkdir(parents=True, exist_ok=True)
    F02_OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(timing_path, F02_IN / "timing.json")
    shutil.copy2(F01_OUT / "audio_clean.mp3", F02_IN / "audio_clean.mp3")
    images_dst = F02_IN / "images"
    if images_dst.exists():
        shutil.rmtree(images_dst)
    shutil.copytree(SHARED_IN / "images", images_dst)
    print(f"[G2] F02/IN prêt : timing.json + audio_clean.mp3 + {len(list(images_dst.iterdir()))} images")

    # Exposer le port 8080
    try:
        url_raw = subprocess.check_output(["/app/export-port.sh", "8080"], text=True).strip()
        print(f"\n[G2] Viewer disponible : {url_raw}")
    except Exception:
        print("\n[G2] Viewer disponible sur : http://localhost:8080/")
        print("     (export-port non disponible dans cet env)")

    print("[G2] En attente de validation de roadmap.json...\n")

    subprocess.run([
        sys.executable, str(REPO_ROOT / "CRS_F02_SERVER.py"),
        "--input",  str(F02_IN),
        "--output", str(F02_OUT),
        "--port",   "8080",
    ], cwd=REPO_ROOT)

    roadmap_path = F02_OUT / "roadmap.json"
    if not roadmap_path.exists():
        print("[G2] ERREUR : roadmap.json absent — validez le viewer.")
        sys.exit(1)

    ledger["gate_actuelle"] = "G3"
    ledger.setdefault("etapes_completees", []).append("F02")
    save_ledger(ledger)

    print("\n════════════════════════════════════════════")
    print("  GATE 2 — roadmap.json validée ✅")
    print("  Prochain : python CRS_EXECUTEUR.py --gate G3")
    print("════════════════════════════════════════════\n")

# ─── GATE G3 : Trigger F03 ────────────────────────────────────────────────────

def cmd_gate_g3(token, ledger):
    print("\n═══════════════════════════════════════════")
    print("  CRUSADER — GATE G3 (F03 Remotion)")
    print("═══════════════════════════════════════════\n")

    repo         = ledger["github_repo"]
    run_id       = ledger["run_id"]
    roadmap_path = F02_OUT / "roadmap.json"

    if not roadmap_path.exists():
        print(f"[G3] ERREUR : roadmap.json absent dans {F02_OUT}")
        sys.exit(1)

    with open(F01_OUT / "timing.json") as f:
        timing = json.load(f)
    meta         = timing.get("meta", {})
    total_frames = meta.get("total_frames", 0)
    fps          = meta.get("fps", 30)

    # DELTA-TEST3 : auto-detect CrusaderDelta si roadmap.json contient thumbnail_plan
    roadmap_data = {}
    if roadmap_path.exists():
        with open(roadmap_path) as f:
            roadmap_data = json.load(f)
    plan = roadmap_data.get("thumbnail_plan")
    if plan and plan.get("chapters"):
        composition   = "CrusaderDelta"
        trans_frames  = plan.get("transition_frames", 45)
        n_chapters    = len(plan["chapters"])
        total_frames  = total_frames + trans_frames * n_chapters
        print(f"[G3] Mode DELTA detecte — {n_chapters} chapitres, {trans_frames}f/transition")
        print(f"[G3] Composition : CrusaderDelta — durée totale : {total_frames} frames")
    else:
        composition = ledger.get("f03_meta", {}).get("composition", "CrusaderShort")

    # Vérifier si Release run_id existe, sinon recréer
    h = _h(token)
    r = requests.get(f"{GH_API}/repos/{repo}/releases/tags/{run_id}", headers=h)
    if r.ok:
        upload_url = r.json()["upload_url"].split("{")[0]
        # Ajouter les assets F03 manquants (roadmap + audio si absents)
        upload_asset(upload_url, "roadmap.json", roadmap_path, "application/json", token)
        upload_asset(upload_url, "timing.json",  F01_OUT / "timing.json", "application/json", token)
        upload_asset(upload_url, "audio_clean.mp3", F01_OUT / "audio_clean.mp3", "audio/mpeg", token)
    else:
        # Release expirée ou supprimée — recréer complète
        release    = create_or_reset_release(run_id, f"[CRUSADER] {run_id}", token, repo)
        upload_url = release["upload_url"].split("{")[0]
        upload_asset(upload_url, "roadmap.json", roadmap_path, "application/json", token)
        upload_asset(upload_url, "timing.json",  F01_OUT / "timing.json", "application/json", token)
        upload_asset(upload_url, "audio_clean.mp3", F01_OUT / "audio_clean.mp3", "audio/mpeg", token)
        zip_data, img_count = zip_images(SHARED_IN / "images")
        upload_asset_bytes(upload_url, "images.zip", zip_data, "application/zip", token)
        print(f"[UPLOAD] images.zip ({img_count} images) ✅")

    # DELTA-TEST3 : uploader thumbnail.png si présent (requis pour CrusaderDelta)
    thumb_path = F02_IN / "thumbnail.png"
    if thumb_path.exists():
        upload_asset(upload_url, "thumbnail.png", thumb_path, "image/png", token)
        print(f"[G3] thumbnail.png uploadé vers la release")

    gh_run_id, url = trigger_workflow_and_get_url(
        "f03_render.yml",
        {
            "run_id":       run_id,
            "fps":          str(fps),
            "composition":  composition,
            "total_frames": str(total_frames),
        },
        token, repo,
    )

    ledger.setdefault("gh_runs", {})["f03"] = gh_run_id
    ledger.setdefault("f03_meta", {})["total_frames"] = total_frames
    ledger.setdefault("f03_meta", {})["composition"]  = composition
    ledger["gate_actuelle"] = "G4"
    ledger.setdefault("etapes_completees", []).append("F03_triggered")
    save_ledger(ledger)

    print("\n════════════════════════════════════════════")
    print("  GATE 3 — F03 EN COURS SUR GITHUB ACTIONS")
    print(f"  Surveille : {url}")
    print("  Quand F03 terminé → python CRS_EXECUTEUR.py --gate G4")
    print("════════════════════════════════════════════\n")

# ─── GATE G4 : Télécharger F03 + Trigger F04 ─────────────────────────────────

def cmd_gate_g4(token, ledger):
    print("\n═══════════════════════════════════════════")
    print("  CRUSADER — GATE G4 (F04 Helbrecht)")
    print("═══════════════════════════════════════════\n")

    repo          = ledger["github_repo"]
    run_id        = ledger["run_id"]
    gh_run_id_f03 = ledger.get("gh_runs", {}).get("f03")

    if not gh_run_id_f03:
        print("[G4] ERREUR : run ID F03 absent du ledger.")
        sys.exit(1)

    # Télécharger short_render.mp4 depuis artifact F03
    F03_OUT.mkdir(parents=True, exist_ok=True)
    print("[G4] Téléchargement short_render.mp4...")
    download_artifact_to(gh_run_id_f03, "resultat-final", F03_OUT, token, repo)

    short_render = F03_OUT / "short_render.mp4"
    if not short_render.exists():
        print(f"[G4] ERREUR : short_render.mp4 absent dans {F03_OUT}")
        sys.exit(1)
    print(f"[G4] short_render.mp4 OK — {short_render.stat().st_size / 1024 / 1024:.1f} MB")

    # Créer Release f04 et uploader
    tag_f04  = f"{run_id}-f04"
    release  = create_or_reset_release(tag_f04, f"[CRUSADER] {tag_f04}", token, repo)
    upload_url = release["upload_url"].split("{")[0]
    upload_asset(upload_url, "short_render.mp4", short_render, "video/mp4", token)
    upload_asset(upload_url, "timing.json", F01_OUT / "timing.json", "application/json", token)

    # Trigger F04
    gh_run_id, url = trigger_workflow_and_get_url(
        "f04_helbrecht.yml", {"run_id": run_id}, token, repo
    )

    ledger.setdefault("gh_runs", {})["f04"] = gh_run_id
    ledger["gate_actuelle"] = "CLOSE"
    ledger.setdefault("etapes_completees", []).append("F04_triggered")
    save_ledger(ledger)

    print("\n════════════════════════════════════════════")
    print("  GATE 4 — F04 EN COURS SUR GITHUB ACTIONS")
    print(f"  Surveille : {url}")
    print("  Quand F04 terminé → python CRS_EXECUTEUR.py --close")
    print("════════════════════════════════════════════\n")

# ─── CLOSE ────────────────────────────────────────────────────────────────────

def cmd_close(token, ledger):
    print("\n═══════════════════════════════════════════")
    print("  CRUSADER — CLOSE")
    print("═══════════════════════════════════════════\n")

    repo          = ledger["github_repo"]
    gh_run_id_f04 = ledger.get("gh_runs", {}).get("f04")

    if not gh_run_id_f04:
        print("[CLOSE] ERREUR : run ID F04 absent du ledger.")
        sys.exit(1)

    F04_OUT.mkdir(parents=True, exist_ok=True)
    print("[CLOSE] Téléchargement youtube_final...")
    download_artifact_to(gh_run_id_f04, "youtube-final", F04_OUT, token, repo)

    mp4s = list(F04_OUT.glob("*.mp4"))
    if not mp4s:
        print(f"[CLOSE] ERREUR : aucun .mp4 trouvé dans {F04_OUT}")
        sys.exit(1)

    final = mp4s[0]
    print(f"[CLOSE] Artefact final : {final} ({final.stat().st_size / 1024 / 1024:.1f} MB)")

    ledger["gate_actuelle"]  = "COMPLETED"
    ledger["artefacts"]["youtube_final"] = str(final)
    ledger.setdefault("etapes_completees", []).append("COMPLETED")
    save_ledger(ledger)

    print("\n════════════════════════════════════════════")
    print(f"  Production : {ledger['production_title']}")
    print(f"  Run ID     : {ledger['run_id']}")
    print(f"  Artefact   : {final}")
    print("\n  Victoria Aeterna.\n")
    print("════════════════════════════════════════════\n")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CRS_EXECUTEUR v2 — CRUSADER GitHub Actions")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start",  action="store_true", help="Nouvelle production")
    group.add_argument("--resume", action="store_true", help="Reprendre depuis ledger")
    group.add_argument("--gate",   choices=["G2", "G3", "G4"], help="Avancer après validation")
    group.add_argument("--close",  action="store_true", help="Télécharger artefact final")
    parser.add_argument("--title", help="Titre production (requis avec --start)")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN", "")
    if not token:
        print("ERREUR : GH_TOKEN non défini")
        print("  export GH_TOKEN=<votre_token>")
        sys.exit(1)

    ledger = load_ledger()

    if args.start:
        if not args.title:
            print("ERREUR : --title requis avec --start")
            sys.exit(1)
        cmd_start(args.title, token, ledger)

    elif args.gate == "G2":
        cmd_gate_g2(token, ledger)

    elif args.gate == "G3":
        cmd_gate_g3(token, ledger)

    elif args.gate == "G4":
        cmd_gate_g4(token, ledger)

    elif args.close:
        cmd_close(token, ledger)

    elif args.resume:
        gate = ledger.get("gate_actuelle", "G2")
        print(f"[RESUME] Reprise à gate {gate}")
        if gate == "G2":
            cmd_gate_g2(token, ledger)
        elif gate == "G3":
            cmd_gate_g3(token, ledger)
        elif gate == "G4":
            cmd_gate_g4(token, ledger)
        elif gate == "CLOSE":
            cmd_close(token, ledger)
        else:
            print(f"[RESUME] Production déjà terminée ({gate})")


if __name__ == "__main__":
    main()
