#!/usr/bin/env python3
"""
CRS_CODEDUMP.py — CRUSADER Code Dump
Parcourt tout le repo et produit un fichier TXT unique avec
tout le code annoté (chemin, langage, séparateurs clairs).
Usage : python CRS_CODEDUMP.py [racine_repo] [fichier_sortie]
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

EXTENSIONS_LANG = {
    ".py":    "PYTHON",
    ".jsx":   "JSX (React/Remotion)",
    ".js":    "JAVASCRIPT",
    ".ts":    "TYPESCRIPT",
    ".tsx":   "TSX",
    ".html":  "HTML",
    ".css":   "CSS",
    ".json":  "JSON",
    ".md":    "MARKDOWN",
    ".ipynb": "JUPYTER NOTEBOOK",
    ".txt":   "TEXT",
    ".sh":    "SHELL",
    ".yaml":  "YAML",
    ".yml":   "YAML",
    ".toml":  "TOML",
    ".cfg":   "CONFIG",
    ".config.js": "CONFIG (JS)",
}

# Dossiers et fichiers a ignorer
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    ".venv", "venv", "dist", "build", ".next", ".cache",
}
IGNORE_FILES = {
    ".gitkeep", ".DS_Store", ".env", ".env.local",
}
IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
    ".mp4", ".mp3", ".wav", ".aac",
    ".zip", ".tar", ".gz",
    ".lock",   # package-lock.json, yarn.lock
}

SEP = "=" * 80
MINI_SEP = "-" * 60

# ── Core ──────────────────────────────────────────────────────────────────────

def get_lang(filepath: Path) -> str:
    name = filepath.name.lower()
    # Cas speciaux double extension
    for suffix, lang in EXTENSIONS_LANG.items():
        if name.endswith(suffix):
            return lang
    return "UNKNOWN"

def should_skip(path: Path) -> bool:
    # Dossiers interdits dans le chemin
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True
    if path.name in IGNORE_FILES:
        return True
    if path.suffix.lower() in IGNORE_EXTENSIONS:
        return True
    # Ignorer les fichiers trop lourds (> 500 KB)
    try:
        if path.stat().st_size > 500_000:
            return True
    except OSError:
        return True
    return False

def collect_files(root: Path):
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if should_skip(p):
            continue
        files.append(p)
    return files

def dump(root: Path, output: Path):
    files = collect_files(root)
    total = len(files)

    with open(output, "w", encoding="utf-8") as f:
        # En-tete
        f.write(f"{SEP}\n")
        f.write(f"  CRUSADER — CODE DUMP COMPLET\n")
        f.write(f"  Genere le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Racine    : {root.resolve()}\n")
        f.write(f"  Fichiers  : {total}\n")
        f.write(f"{SEP}\n\n")

        # Table des matieres
        f.write("TABLE DES MATIERES\n")
        f.write(f"{MINI_SEP}\n")
        for i, p in enumerate(files, 1):
            rel = p.relative_to(root)
            lang = get_lang(p)
            f.write(f"  [{i:03d}] {rel}  [{lang}]\n")
        f.write(f"\n{SEP}\n\n")

        # Contenu fichier par fichier
        for i, p in enumerate(files, 1):
            rel = p.relative_to(root)
            lang = get_lang(p)
            size = p.stat().st_size

            f.write(f"{SEP}\n")
            f.write(f"  FICHIER [{i:03d}/{total}]\n")
            f.write(f"  Chemin   : {rel}\n")
            f.write(f"  Langage  : {lang}\n")
            f.write(f"  Taille   : {size} octets\n")
            f.write(f"{SEP}\n\n")

            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                f.write(content)
                if not content.endswith("\n"):
                    f.write("\n")
            except Exception as e:
                f.write(f"[ERREUR LECTURE : {e}]\n")

            f.write(f"\n{MINI_SEP}\n")
            f.write(f"  FIN FICHIER : {rel}\n")
            f.write(f"{MINI_SEP}\n\n")

        # Pied de page
        f.write(f"{SEP}\n")
        f.write(f"  FIN DU DUMP — {total} fichiers traites\n")
        f.write(f"{SEP}\n")

    return total

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    out_name = sys.argv[2] if len(sys.argv) > 2 else "CRUSADER_CODEDUMP.txt"
    output = Path(out_name)

    if not root.exists():
        print(f"[ERREUR] Racine introuvable : {root}")
        sys.exit(1)

    print(f"[CRS_CODEDUMP] Scan de : {root.resolve()}")
    total = dump(root, output)
    size_kb = output.stat().st_size // 1024
    print(f"[CRS_CODEDUMP] {total} fichiers — {size_kb} KB → {output}")
