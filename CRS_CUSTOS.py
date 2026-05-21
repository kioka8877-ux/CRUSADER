"""
CRS_CUSTOS.py — Gardien de Flotte CRUSADER
===========================================
Valide les fichiers IN/ et OUT/ de chaque frégate avant et après tout transfert.
Stdlib uniquement — aucune dépendance externe.

Usage:
    python CRS_CUSTOS.py --frigate F01 --mode check-out [--drive-base /path]
    python CRS_CUSTOS.py --frigate F02 --mode check-in  [--drive-base /path]

Exit codes:
    0 = VALIDATION OK
    1 = VALIDATION FAIL
"""

import argparse
import json
import os
import sys

# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_DRIVE_BASE = "/content/drive/MyDrive/DRIVE_CRUSADER"

# Manifeste de validation par frégate et par mode
MANIFEST = {
    "SHARED": {
        "check-out": {
            "files": [
                {"path": "audio_clean.mp3", "type": "file", "min_size": 10000},
            ],
            "dirs": ["images"],
        }
    },
    "F01": {
        "check-out": {
            "files": [
                {"path": "F01_GRIMALDUS/IN/audio_clean.mp3", "type": "file", "min_size": 10000},
            ]
        },
        "check-in": {
            "files": [
                {"path": "F01_GRIMALDUS/OUT/timing.json", "type": "json", "required_keys": ["meta", "words", "segments"]},
            ]
        },
    },
    "F02": {
        "check-out": {
            "files": [
                {"path": "F02_CASTELLAN/IN/timing.json", "type": "json", "required_keys": ["meta", "words", "segments"]},
            ],
            "dirs": ["F02_CASTELLAN/IN/images"],
        },
        "check-in": {
            "files": [
                {"path": "F02_CASTELLAN/OUT/roadmap.json", "type": "json", "required_keys": ["meta", "timeline", "style", "validated_by_magos"]},
            ]
        },
    },
    "F03": {
        "check-out": {
            "files": [
                {"path": "F03_SIGISMUND/IN/timing.json",   "type": "json",  "required_keys": ["meta", "words", "segments"]},
                {"path": "F03_SIGISMUND/IN/roadmap.json",  "type": "json",  "required_keys": ["meta", "timeline", "style", "validated_by_magos"]},
                {"path": "F03_SIGISMUND/IN/audio_clean.mp3","type": "file", "min_size": 10000},
            ],
            "dirs": ["F03_SIGISMUND/IN/images"],
        },
        "check-in": {
            "files": [
                {"path": "F03_SIGISMUND/OUT/short_render.mp4", "type": "file", "min_size": 100000},
            ]
        },
    },
    "F04": {
        "check-out": {
            "files": [
                {"path": "F04_HELBRECHT/IN/short_render.mp4", "type": "file", "min_size": 100000},
                {"path": "F04_HELBRECHT/IN/timing.json",       "type": "json", "required_keys": ["meta"]},
            ]
        },
        "check-in": {
            "files": [
                {"path": "F04_HELBRECHT/OUT/final_master.mp4", "type": "file", "min_size": 100000},
            ]
        },
    },
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def log_ok(msg):
    print(f"  [OK]   {msg}")

def log_fail(msg):
    print(f"  [FAIL] {msg}")

def log_info(msg):
    print(f"  [...]  {msg}")

def validate_file(full_path, spec):
    """Validate a single file entry from the manifest."""
    if not os.path.exists(full_path):
        log_fail(f"Fichier absent : {full_path}")
        return False

    if spec.get("type") == "json":
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            log_fail(f"JSON invalide ({full_path}) : {e}")
            return False
        for key in spec.get("required_keys", []):
            if key not in data:
                log_fail(f"Clé manquante '{key}' dans {full_path}")
                return False
        log_ok(f"{full_path}")
        return True

    if spec.get("type") == "file":
        size = os.path.getsize(full_path)
        min_size = spec.get("min_size", 0)
        if size < min_size:
            log_fail(f"Fichier trop petit ({size} bytes < {min_size}) : {full_path}")
            return False
        log_ok(f"{full_path} ({size:,} bytes)")
        return True

    log_ok(full_path)
    return True

def validate_dir(full_path):
    """Check a directory exists and is not empty."""
    if not os.path.isdir(full_path):
        log_fail(f"Dossier absent : {full_path}")
        return False
    contents = os.listdir(full_path)
    if not contents:
        log_fail(f"Dossier vide : {full_path}")
        return False
    log_ok(f"{full_path}/ ({len(contents)} fichier(s))")
    return True

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CRS_CUSTOS — Gardien de Flotte CRUSADER")
    parser.add_argument("--frigate", required=True, choices=["SHARED", "F01", "F02", "F03", "F04"])
    parser.add_argument("--mode",    required=True, choices=["check-out", "check-in"])
    parser.add_argument("--drive-base", default=DEFAULT_DRIVE_BASE)
    args = parser.parse_args()

    base = args.drive_base
    frigate = args.frigate
    mode = args.mode

    print()
    print(f"═══════════════════════════════════════════════")
    print(f"  CRS_CUSTOS — {frigate} — {mode.upper()}")
    print(f"  Drive base : {base}")
    print(f"═══════════════════════════════════════════════")

    spec = MANIFEST.get(frigate, {}).get(mode)
    if spec is None:
        print(f"  [INFO] Aucune validation définie pour {frigate} / {mode}. Passage autorisé.")
        sys.exit(0)

    errors = 0

    for file_spec in spec.get("files", []):
        full = os.path.join(base, file_spec["path"])
        log_info(f"Vérification : {file_spec['path']}")
        if not validate_file(full, file_spec):
            errors += 1

    for dir_path in spec.get("dirs", []):
        full = os.path.join(base, dir_path)
        log_info(f"Vérification dossier : {dir_path}")
        if not validate_dir(full):
            errors += 1

    print()
    if errors == 0:
        print(f"  VALIDATION OK — {frigate} {mode} : Aucune erreur.")
        print(f"═══════════════════════════════════════════════")
        sys.exit(0)
    else:
        print(f"  VALIDATION FAIL — {errors} erreur(s) détectée(s). Transit interdit.")
        print(f"═══════════════════════════════════════════════")
        sys.exit(1)

if __name__ == "__main__":
    main()
