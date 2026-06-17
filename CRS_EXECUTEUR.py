"""
CRS_EXECUTEUR.py — Orchestrateur CRUSADER (Rubicon Primaris)
=============================================================
Opéré par Claude Exécuteur dans un sandbox jetable.
4 portes opérateur. Zéro Colab.

Usage:
    python CRS_EXECUTEUR.py --start --title "Mon sujet"   # Nouvelle production
    python CRS_EXECUTEUR.py --resume                       # Reprendre depuis ledger
    python CRS_EXECUTEUR.py --gate G2                      # Avancer après validation G2
    python CRS_EXECUTEUR.py --gate G3                      # Avancer après validation G3
    python CRS_EXECUTEUR.py --gate G4                      # Clôturer production

Variables d'environnement requises:
    GH_TOKEN   — token GitHub (scope: repo)
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ─── Chemins ──────────────────────────────────────────────────────────────────

REPO_ROOT   = Path(__file__).parent.resolve()
LEDGER_FILE = REPO_ROOT / "crs_ledger.json"

# Chemins des frégates (relatifs à REPO_ROOT)
F01A_IN   = REPO_ROOT / "F01_GRIMALDUS" / "F01A_CASTELLAN_AUDIO" / "IN"
F01A_OUT  = REPO_ROOT / "F01_GRIMALDUS" / "F01A_CASTELLAN_AUDIO" / "OUT"
F01A_CODE = REPO_ROOT / "F01_GRIMALDUS" / "F01A_CASTELLAN_AUDIO" / "CODEBASE"
F01B_IN   = REPO_ROOT / "F01_GRIMALDUS" / "F01B_GRIMALDUS" / "IN"
F01B_OUT  = REPO_ROOT / "F01_GRIMALDUS" / "OUT"
F01B_CODE = REPO_ROOT / "F01_GRIMALDUS" / "F01B_GRIMALDUS" / "CODEBASE"
F02_IN    = REPO_ROOT / "F02_CASTELLAN" / "IN"
F02_OUT   = REPO_ROOT / "F02_CASTELLAN" / "OUT"
F02_CODE  = REPO_ROOT / "F02_CASTELLAN" / "CODEBASE"
F03_IN    = REPO_ROOT / "F03_SIGISMUND" / "IN"
F03_OUT   = REPO_ROOT / "F03_SIGISMUND" / "OUT"
F03_CODE  = REPO_ROOT / "F03_SIGISMUND" / "CODEBASE"
F04_IN    = REPO_ROOT / "F04_HELBRECHT" / "IN"
F04_OUT   = REPO_ROOT / "F04_HELBRECHT" / "OUT"
F04_CODE  = REPO_ROOT / "F04_HELBRECHT" / "CODEBASE"
SHARED_IN = REPO_ROOT / "SHARED" / "IN"

# ─── Ledger ───────────────────────────────────────────────────────────────────

def load_ledger() -> dict:
    with open(LEDGER_FILE) as f:
        return json.load(f)

def save_ledger(ledger: dict):
    ledger["derniere_mise_a_jour"] = datetime.datetime.now().isoformat()
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
    # Commit ledger dans git
    subprocess.run(
        ["git", "add", "crs_ledger.json"],
        cwd=REPO_ROOT, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", f"[LEDGER] {ledger.get('gate_actuelle','?')} — {ledger.get('production_title','?')}"],
        cwd=REPO_ROOT, capture_output=True
    )
    token = os.environ.get("GH_TOKEN", "")
    if token:
        remote = f"https://{token}@github.com/{ledger['github_repo']}.git"
        subprocess.run(
            ["git", "push", remote, "main"],
            cwd=REPO_ROOT, capture_output=True
        )

# ─── CUSTOS ───────────────────────────────────────────────────────────────────

def custos(frigate: str, mode: str) -> bool:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "CRS_CUSTOS.py"),
         "--frigate", frigate, "--mode", mode,
         "--drive-base", str(REPO_ROOT)],
        cwd=REPO_ROOT
    )
    return result.returncode == 0

# ─── GATE 1 : F01A (headless) + F01B + F02 viewer ────────────────────────────

def run_gate_1(ledger: dict):
    print("\n═══════════════════════════════════════════")
    print("  GATE 1 — F01A → F01B → F02 viewer")
    print("═══════════════════════════════════════════\n")

    # Vérifier audio_raw.mp3 dans SHARED/IN
    audio_raw = SHARED_IN / "audio_raw.mp3"
    if not audio_raw.exists():
        print(f"[GATE1] ERREUR : audio_raw.mp3 manquant dans {SHARED_IN}")
        print("        Déposez le fichier et relancez.")
        sys.exit(1)

    images_src = SHARED_IN / "images"
    if not images_src.exists() or not any(images_src.iterdir()):
        print(f"[GATE1] ERREUR : dossier images/ manquant ou vide dans {SHARED_IN}")
        sys.exit(1)

    # Copier audio_raw → F01A/IN
    F01A_IN.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio_raw, F01A_IN / "audio_raw.mp3")
    print(f"[F01A] audio_raw.mp3 copié vers {F01A_IN}")

    # CUSTOS check-out F01A
    if not custos("F01A", "check-out"):
        print("[F01A] CUSTOS check-out FAIL")
        sys.exit(1)

    # F01A headless — import direct, pas de Flask
    sys.path.insert(0, str(F01A_CODE))
    from crs_f01a import remove_silences, detect_silences
    F01A_OUT.mkdir(parents=True, exist_ok=True)
    audio_in_path  = str(F01A_IN / "audio_raw.mp3")
    audio_out_path = str(F01A_OUT / "audio_clean.mp3")
    print("[F01A] Suppression silences (-40dB)...")
    remove_silences(audio_in_path, audio_out_path, threshold_db=-40.0, min_duration=0.5)
    silences = detect_silences(audio_in_path, -40.0, 0.5)
    with open(F01A_OUT / "silence_map.json", "w") as f:
        json.dump({"silences": silences, "silence_count": len(silences)}, f, indent=2)
    print(f"[F01A] audio_clean.mp3 produit — {len(silences)} silences supprimés")

    # CUSTOS check-in F01A
    if not custos("F01A", "check-in"):
        print("[F01A] CUSTOS check-in FAIL")
        sys.exit(1)

    # Copier audio_clean → F01B/IN et F01_GRIMALDUS/IN
    F01B_IN.mkdir(parents=True, exist_ok=True)
    f01_in = REPO_ROOT / "F01_GRIMALDUS" / "IN"
    f01_in.mkdir(parents=True, exist_ok=True)
    shutil.copy2(F01A_OUT / "audio_clean.mp3", F01B_IN / "audio_clean.mp3")
    shutil.copy2(F01A_OUT / "audio_clean.mp3", f01_in / "audio_clean.mp3")
    print("[F01B] audio_clean.mp3 copié vers F01B/IN")

    # CUSTOS check-out F01
    if not custos("F01", "check-out"):
        print("[F01B] CUSTOS check-out FAIL")
        sys.exit(1)

    # F01B — transcription
    F01B_OUT.mkdir(parents=True, exist_ok=True)
    print("[F01B] Transcription faster-whisper...")
    result = subprocess.run(
        [sys.executable, str(F01B_CODE / "crs_f01_grimaldus.py"),
         "--input", str(F01B_IN),
         "--output", str(F01B_OUT)],
        cwd=REPO_ROOT
    )
    if result.returncode != 0:
        print("[F01B] ERREUR transcription")
        sys.exit(1)

    # CUSTOS check-in F01
    if not custos("F01", "check-in"):
        print("[F01B] CUSTOS check-in FAIL")
        sys.exit(1)

    # Lire total_frames depuis timing.json
    with open(F01B_OUT / "timing.json") as f:
        timing = json.load(f)
    total_frames = timing["meta"]["total_frames"]
    ledger["f03_meta"]["total_frames"] = total_frames
    ledger["artefacts"]["timing_json"] = str(F01B_OUT / "timing.json")
    ledger["artefacts"]["audio_clean"] = str(F01A_OUT / "audio_clean.mp3")

    # Préparer F02/IN
    F02_IN.mkdir(parents=True, exist_ok=True)
    shutil.copy2(F01B_OUT / "timing.json", F02_IN / "timing.json")
    images_dst = F02_IN / "images"
    if images_dst.exists():
        shutil.rmtree(images_dst)
    shutil.copytree(images_src, images_dst)
    print(f"[F02] timing.json + {len(list(images_src.iterdir()))} images copiés vers F02/IN")

    # CUSTOS check-out F02
    if not custos("F02", "check-out"):
        print("[F02] CUSTOS check-out FAIL")
        sys.exit(1)

    # Mettre à jour ledger
    ledger["gate_actuelle"] = "G2"
    ledger["etapes_completees"].append("F01A")
    ledger["etapes_completees"].append("F01B")
    save_ledger(ledger)

    # Lancer F02 viewer
    print("\n[F02] Lancement viewer sur port 5002...")
    print("════════════════════════════════════════════")
    print("  GATE 2 — ACTION OPÉRATEUR REQUISE")
    print(f"  Ouvrir : http://localhost:5002/")
    print("  Valider roadmap.json dans le viewer")
    print("  Puis : python CRS_EXECUTEUR.py --gate G2")
    print("════════════════════════════════════════════\n")

    subprocess.run(
        [sys.executable, str(F02_CODE / "crs_f02_castellan.py"),
         "--input", str(F02_IN),
         "--output", str(F02_OUT),
         "--viewer", str(F02_CODE / "crs_f02_viewer.html"),
         "--port", "5002"],
        cwd=REPO_ROOT
    )

# ─── GATE 2 : F03 (upload + trigger + poll + download) ───────────────────────

def run_gate_2(ledger: dict):
    print("\n═══════════════════════════════════════════")
    print("  GATE 2 — F03 GitHub Actions")
    print("═══════════════════════════════════════════\n")

    gh_token = os.environ.get("GH_TOKEN", "")
    if not gh_token:
        print("[F03] ERREUR : GH_TOKEN non défini")
        sys.exit(1)

    roadmap_path = F02_OUT / "roadmap.json"
    if not roadmap_path.exists():
        print(f"[F03] ERREUR : roadmap.json manquant dans {F02_OUT}")
        print("      Avez-vous validé le viewer F02 ?")
        sys.exit(1)

    # CUSTOS check-in F02
    if not custos("F02", "check-in"):
        print("[F02] CUSTOS check-in FAIL")
        sys.exit(1)

    # Préparer F03/IN
    F03_IN.mkdir(parents=True, exist_ok=True)
    shutil.copy2(F02_OUT / "roadmap.json", F03_IN / "roadmap.json")
    shutil.copy2(F01B_OUT / "timing.json", F03_IN / "timing.json")
    shutil.copy2(F01A_OUT / "audio_clean.mp3", F03_IN / "audio_clean.mp3")
    images_dst = F03_IN / "images"
    if images_dst.exists():
        shutil.rmtree(images_dst)
    shutil.copytree(SHARED_IN / "images", images_dst)
    print("[F03] Assets préparés dans F03/IN")

    # CUSTOS check-out F03
    if not custos("F03", "check-out"):
        print("[F03] CUSTOS check-out FAIL")
        sys.exit(1)

    # Import F03 functions
    sys.path.insert(0, str(F03_CODE))
    from crs_f03_gh_trigger import (
        upload_assets_to_release,
        trigger_workflow,
        poll_run_status,
        download_final_artifact,
    )

    run_id   = ledger["run_id"]
    repo     = ledger["github_repo"]
    fps      = ledger["f03_meta"]["fps"]
    comp     = ledger["f03_meta"]["composition"]
    frames   = ledger["f03_meta"]["total_frames"]

    print(f"[F03] Upload assets — run_id={run_id}")
    upload_assets_to_release(str(F03_IN), run_id, gh_token, repo)

    print("[F03] Déclenchement GitHub Actions...")
    gh_run_id = trigger_workflow(run_id, fps, comp, frames, gh_token, repo)
    ledger["gh_actions"]["gh_run_id"] = gh_run_id
    save_ledger(ledger)

    print("[F03] Poll statut...")
    poll_run_status(gh_run_id, gh_token, repo, timeout_min=90)

    F03_OUT.mkdir(parents=True, exist_ok=True)
    mp4_path = download_final_artifact(gh_run_id, run_id, gh_token, repo, str(F03_OUT))
    print(f"[F03] short_render.mp4 téléchargé : {mp4_path}")

    # CUSTOS check-in F03
    if not custos("F03", "check-in"):
        print("[F03] CUSTOS check-in FAIL")
        sys.exit(1)

    ledger["artefacts"]["short_render"] = mp4_path
    ledger["gh_actions"]["status"] = "success"
    ledger["gate_actuelle"] = "G3"
    ledger["etapes_completees"].append("F03")
    save_ledger(ledger)

    print("\n════════════════════════════════════════════")
    print("  GATE 3 — ACTION OPÉRATEUR REQUISE")
    print(f"  Valider : {mp4_path}")
    print("  Puis : python CRS_EXECUTEUR.py --gate G3")
    print("════════════════════════════════════════════\n")

# ─── GATE 3 : F04 ─────────────────────────────────────────────────────────────

def run_gate_3(ledger: dict):
    print("\n═══════════════════════════════════════════")
    print("  GATE 3 — F04 HELBRECHT")
    print("═══════════════════════════════════════════\n")

    short_render = F03_OUT / "short_render.mp4"
    if not short_render.exists():
        print(f"[F04] ERREUR : short_render.mp4 manquant dans {F03_OUT}")
        sys.exit(1)

    # Préparer F04/IN
    F04_IN.mkdir(parents=True, exist_ok=True)
    shutil.copy2(short_render, F04_IN / "short_render.mp4")
    shutil.copy2(F01B_OUT / "timing.json", F04_IN / "timing.json")
    print("[F04] short_render.mp4 + timing.json copiés vers F04/IN")

    # CUSTOS check-out F04
    if not custos("F04", "check-out"):
        print("[F04] CUSTOS check-out FAIL")
        sys.exit(1)

    # F04
    F04_OUT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(F04_CODE / "crs_f04_helbrecht.py"),
         "--input", str(F04_IN),
         "--output", str(F04_OUT)],
        cwd=REPO_ROOT
    )
    if result.returncode != 0:
        print("[F04] ERREUR assemblage final")
        sys.exit(1)

    # CUSTOS check-in F04
    if not custos("F04", "check-in"):
        print("[F04] CUSTOS check-in FAIL")
        sys.exit(1)

    youtube_final = list(F04_OUT.glob("*.mp4"))
    if not youtube_final:
        print(f"[F04] ERREUR : aucun .mp4 trouvé dans {F04_OUT}")
        sys.exit(1)

    final_path = str(youtube_final[0])
    ledger["artefacts"]["youtube_final"] = final_path
    ledger["gate_actuelle"] = "G4"
    ledger["etapes_completees"].append("F04")
    save_ledger(ledger)

    print("\n════════════════════════════════════════════")
    print("  GATE 4 — ACTION OPÉRATEUR REQUISE")
    print(f"  Valider et uploader : {final_path}")
    print("  Puis : python CRS_EXECUTEUR.py --gate G4")
    print("════════════════════════════════════════════\n")

# ─── GATE 4 : Clôture ─────────────────────────────────────────────────────────

def run_gate_4(ledger: dict):
    print("\n═══════════════════════════════════════════")
    print("  GATE 4 — CLÔTURE PRODUCTION")
    print("═══════════════════════════════════════════\n")

    ledger["gate_actuelle"] = "COMPLETED"
    ledger["etapes_completees"].append("GATE4_CLOSED")
    save_ledger(ledger)

    print(f"  Production : {ledger['production_title']}")
    print(f"  Run ID     : {ledger['run_id']}")
    print(f"  Artefact   : {ledger['artefacts']['youtube_final']}")
    print(f"  Étapes     : {', '.join(ledger['etapes_completees'])}")
    print("\n  Victoria Aeterna.\n")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CRS_EXECUTEUR — Orchestrateur CRUSADER Rubicon")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start",  action="store_true", help="Nouvelle production")
    group.add_argument("--resume", action="store_true", help="Reprendre depuis ledger")
    group.add_argument("--gate",   choices=["G2", "G3", "G4"], help="Avancer après validation opérateur")
    parser.add_argument("--title", help="Titre de la production (requis avec --start)")
    args = parser.parse_args()

    ledger = load_ledger()

    if args.start:
        if not args.title:
            print("ERREUR : --title requis avec --start")
            sys.exit(1)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        ledger["run_id"]           = f"CRS_{ts}"
        ledger["production_title"] = args.title
        ledger["gate_actuelle"]    = "G1"
        ledger["etapes_completees"] = []
        ledger["repo_root"]        = str(REPO_ROOT)
        save_ledger(ledger)
        run_gate_1(ledger)

    elif args.resume:
        gate = ledger.get("gate_actuelle", "G1")
        print(f"[RESUME] Reprise à {gate}")
        if gate == "G1":
            run_gate_1(ledger)
        elif gate == "G2":
            run_gate_2(ledger)
        elif gate == "G3":
            run_gate_3(ledger)
        elif gate == "G4":
            run_gate_4(ledger)
        else:
            print(f"[RESUME] Production déjà terminée ({gate})")

    elif args.gate:
        if args.gate == "G2":
            run_gate_2(ledger)
        elif args.gate == "G3":
            run_gate_3(ledger)
        elif args.gate == "G4":
            run_gate_4(ledger)


if __name__ == "__main__":
    main()
