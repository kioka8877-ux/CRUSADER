"""
crs_f03_modal_worker.py — Modal Worker pour F03 SIGISMUND
=========================================================
Rendu Remotion distribué en parallèle sur GPU Modal.

Usage depuis le notebook Colab :
    import modal
    # Voir CRS_F03.ipynb Étape 7 — Dispatch Modal

Architecture :
    Colab monte Drive → lit assets → upload_assets() vers Modal Volume
    → N × render_chunk() sur GPU A10G en parallèle (--frames=FROM-TO)
    → concat_chunks() FFmpeg → short_render.mp4 en bytes
    → Colab écrit sur Drive F03/OUT/
"""

import modal

# ─── Constantes ───────────────────────────────────────────────────────────────

REPO_RAW    = "https://raw.githubusercontent.com/kioka8877-ux/CRUSADER/main"
PROJECT_DIR = "/remotion_project"
VOLUME_MOUNT = "/assets"

# ─── Image ────────────────────────────────────────────────────────────────────
# Node.js 20 + Chromium + FFmpeg + npm install Remotion (mis en cache dans l'image)

def _build_remotion_project():
    """Télécharge les sources Remotion et lance npm install (appelé au build de l'image)."""
    import urllib.request
    import subprocess
    import os

    files = [
        ("F03_SIGISMUND/CODEBASE/package.json",                     "package.json"),
        ("F03_SIGISMUND/CODEBASE/remotion.config.js",               "remotion.config.js"),
        ("F03_SIGISMUND/CODEBASE/src/index.jsx",                    "src/index.jsx"),
        ("F03_SIGISMUND/CODEBASE/src/Root.jsx",                     "src/Root.jsx"),
        ("F03_SIGISMUND/CODEBASE/src/Main.jsx",                     "src/Main.jsx"),
        ("F03_SIGISMUND/CODEBASE/src/components/Scene.jsx",         "src/components/Scene.jsx"),
        ("F03_SIGISMUND/CODEBASE/src/components/Subtitle.jsx",      "src/components/Subtitle.jsx"),
        ("F03_SIGISMUND/CODEBASE/src/components/Background.jsx",    "src/components/Background.jsx"),
    ]

    for rel, dest in files:
        full_dest = os.path.join(PROJECT_DIR, dest)
        os.makedirs(os.path.dirname(full_dest), exist_ok=True)
        urllib.request.urlretrieve(f"{REPO_RAW}/{rel}", full_dest)
        print(f"[BUILD] {dest}")

    subprocess.run(["npm", "install", "--prefer-offline"], cwd=PROJECT_DIR, check=True)
    print("[BUILD] npm install OK")


image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "curl", "gnupg", "ffmpeg", "ca-certificates",
        "chromium", "fonts-liberation",
        "libatk-bridge2.0-0", "libdrm2", "libxkbcommon0",
        "libgbm1", "libasound2",
    )
    .run_commands(
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
    )
    .run_function(_build_remotion_project)
)

# ─── App + Volume ─────────────────────────────────────────────────────────────

app    = modal.App("crusader-f03-renderer", image=image)
volume = modal.Volume.from_name("crusader-assets", create_if_missing=True)

# ─── upload_assets ────────────────────────────────────────────────────────────

@app.function(volumes={VOLUME_MOUNT: volume}, timeout=300)
def upload_assets(assets: dict):
    """
    Reçoit les assets sous forme de dict {chemin_relatif: bytes}.
    Exemples de clés : "timing.json", "roadmap.json", "audio_clean.mp3",
                       "images/frame_001.png", ...
    Les écrit dans le Volume sous /assets/public/.
    """
    import os

    for rel_path, data in assets.items():
        dest = os.path.join(VOLUME_MOUNT, "public", rel_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        print(f"[UPLOAD] {rel_path} — {len(data) / 1024:.1f} KB")

    volume.commit()
    print(f"[UPLOAD] {len(assets)} fichier(s) versé(s) dans le Volume.")


# ─── render_chunk ─────────────────────────────────────────────────────────────

@app.function(
    gpu="A10G",
    volumes={VOLUME_MOUNT: volume},
    timeout=1800,
    memory=8192,
)
def render_chunk(chunk_id: int, from_frame: int, to_frame: int, composition: str = "CrusaderShort") -> bytes:
    """
    Rend les frames [from_frame, to_frame] et retourne le chunk .mp4 en bytes.
    """
    import shutil
    import subprocess
    import os

    # Copie les assets du Volume dans public/ du projet Remotion
    public_src  = os.path.join(VOLUME_MOUNT, "public")
    public_dest = os.path.join(PROJECT_DIR, "public")
    if os.path.exists(public_dest):
        shutil.rmtree(public_dest)
    shutil.copytree(public_src, public_dest)
    print(f"[CHUNK {chunk_id}] Assets copiés ({public_dest})")

    # Détection Chromium
    chrome = ""
    for candidate in ["chromium", "chromium-browser"]:
        r = subprocess.run(["which", candidate], capture_output=True, text=True)
        if r.returncode == 0:
            chrome = r.stdout.strip()
            break

    chunk_file = f"/tmp/chunk_{chunk_id:03d}.mp4"

    cmd = [
        "npx", "--yes", "remotion", "render",
        "src/index.jsx",
        composition,
        chunk_file,
        "--gl=swangle",
        f"--frames={from_frame}-{to_frame}",
    ]
    if chrome:
        cmd.append(f"--browser-executable={chrome}")

    print(f"[CHUNK {chunk_id}] Rendu frames {from_frame}→{to_frame}...")
    result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True)
    print(result.stdout[-3000:] if result.stdout else '')

    if result.returncode != 0:
        raise RuntimeError(
            f"Chunk {chunk_id} : exit {result.returncode}\n"
            f"STDOUT:\n{result.stdout[-2000:]}\n"
            f"STDERR:\n{result.stderr[-2000:]}"
        )

    with open(chunk_file, "rb") as f:
        data = f.read()

    print(f"[CHUNK {chunk_id}] OK — {len(data) / 1024 / 1024:.1f} MB")
    return data


# ─── concat_chunks ────────────────────────────────────────────────────────────

@app.function(image=image, timeout=300)
def concat_chunks(chunks_data: list, output_name: str = "short_render.mp4") -> bytes:
    """
    Concatène N chunks .mp4 avec FFmpeg (copy stream, sans ré-encodage).
    Retourne la vidéo finale en bytes.
    """
    import subprocess
    import tempfile
    import os

    tmp_dir = tempfile.mkdtemp()
    list_path = os.path.join(tmp_dir, "chunks_list.txt")

    with open(list_path, "w") as lst:
        for i, data in enumerate(chunks_data):
            path = os.path.join(tmp_dir, f"chunk_{i:03d}.mp4")
            with open(path, "wb") as f:
                f.write(data)
            lst.write(f"file '{path}'\n")
            print(f"[CONCAT] chunk_{i:03d}.mp4 — {len(data) / 1024 / 1024:.1f} MB")

    output_path = os.path.join(tmp_dir, output_name)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path,
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError("FFmpeg concat échoué")

    with open(output_path, "rb") as f:
        data = f.read()

    print(f"[CONCAT] Vidéo finale — {len(data) / 1024 / 1024:.1f} MB")
    return data
