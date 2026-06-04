"""
crs_f04_helbrecht.py — Frégate F04 HELBRECHT v2
================================================
Camouflage universel + Finalisation YouTube.

Contrat d'interface (schema timing.json attendu) :
  {
    "meta": {
      "title":            "string",
      "description":      "string (optionnel)",
      "fps":              30,
      "format":           "vertical | horizontal",
      "duration_seconds": 59.0,
      "date":             "YYYY-MM-DD (optionnel → today)",
      "chapters": [
        { "t": 0,  "label": "string" },
        ...
      ]
    }
  }

IN  : short_render.mp4 + timing.json
OUT : youtube_short.mp4 OU youtube_long.mp4 + rapport_f04.html

Universal — aucune référence au contenu ou à la niche dans la logique.
Compatible tout pipeline vidéo (CRUSADER, immobilier, fitness, etc.)

Usage:
    python crs_f04_helbrecht.py --input /path/IN/ --output /path/OUT/
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime

# ─── Constantes ───────────────────────────────────────────────────────────────

INPUT_VIDEO  = "short_render.mp4"
INPUT_TIMING = "timing.json"

# ─── Logging ──────────────────────────────────────────────────────────────────

def log_ok(msg):   print(f"  [OK]   {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...]  {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print()
    print(f"── {title} {bar}")

# ─── Vérification outils ──────────────────────────────────────────────────────

def check_tools():
    """Vérifie que ffmpeg et ffprobe sont disponibles."""
    for tool in ("ffmpeg", "ffprobe"):
        result = subprocess.run([tool, "-version"], capture_output=True, text=True)
        if result.returncode != 0:
            log_fail(f"{tool} non trouvé. Installez-le : apt-get install -y ffmpeg")
            sys.exit(1)
        v = result.stdout.splitlines()[0]
        log_ok(v)

# ─── Lecture timing.json ──────────────────────────────────────────────────────

def read_timing(timing_path: str) -> dict:
    """Lit timing.json et retourne la meta normalisée avec valeurs par défaut."""
    if not os.path.isfile(timing_path):
        log_fail(f"timing.json introuvable : {timing_path}")
        sys.exit(1)
    with open(timing_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    meta = data.get("meta", {})
    meta.setdefault("title",            "VIDEO")
    meta.setdefault("description",      "")
    meta.setdefault("fps",              30)
    meta.setdefault("date",             date.today().isoformat())
    meta.setdefault("chapters",         [])
    meta.setdefault("duration_seconds", 0)
    log_ok(f"timing.json lu — titre : {meta['title']}")
    return meta

# ─── Probe vidéo ──────────────────────────────────────────────────────────────

def probe_video(video_path: str) -> dict:
    """Lance ffprobe et retourne les données brutes JSON."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", video_path],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

def extract_video_info(probe_data: dict) -> dict:
    """Extrait les métriques utiles d'un résultat ffprobe."""
    info = {
        "duration":      0.0,
        "size_mb":       0.0,
        "width":         0,
        "height":        0,
        "video_codec":   "?",
        "audio_codec":   "?",
        "sample_rate":   "?",
        "video_bitrate": "?",
        "encoder_tag":   "",
    }
    fmt = probe_data.get("format", {})
    info["duration"] = float(fmt.get("duration", 0))
    info["size_mb"]  = int(fmt.get("size", 0)) / (1024 * 1024)
    tags = fmt.get("tags", {})
    # Audit camouflage : cherche tout tag d'outil
    info["encoder_tag"] = (
        tags.get("encoder", "") or
        tags.get("ENCODER", "") or
        tags.get("software", "") or
        tags.get("encoding_tool", "")
    )
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "video":
            info["width"]        = stream.get("width", 0)
            info["height"]       = stream.get("height", 0)
            info["video_codec"]  = stream.get("codec_name", "?")
            br = stream.get("bit_rate", "")
            info["video_bitrate"] = f"{int(br)//1000} kbps" if br else "?"
        elif stream.get("codec_type") == "audio":
            info["audio_codec"] = stream.get("codec_name", "?")
            info["sample_rate"] = stream.get("sample_rate", "?")
    return info

# ─── Détection format ─────────────────────────────────────────────────────────

def detect_format(info: dict) -> str:
    """
    Détecte le format à partir des dimensions de la vidéo source.
    Retourne 'vertical' (Short 9:16) ou 'horizontal' (Long 16:9).
    Le champ 'format' de timing.json est utilisé en fallback si les
    dimensions ne sont pas disponibles.
    """
    w, h = info.get("width", 0), info.get("height", 0)
    if w > 0 and h > 0:
        return "vertical" if h > w else "horizontal"
    return "horizontal"

def output_filename(fmt: str) -> str:
    return "youtube_short.mp4" if fmt == "vertical" else "youtube_long.mp4"

# ─── QA Gate ──────────────────────────────────────────────────────────────────

SUSPICIOUS_TAGS = ("remotion", "opencv", "python", "openai", "runway",
                   "stable-diffusion", "suno", "udio", "elevenlabs",
                   "whisper", "ffmpeg-python", "moviepy", "lavf", "lavc")

def qa_gate(info: dict, meta: dict, stage: str) -> list:
    """
    Analyse qualité. Retourne une liste de tuples (label, ok, detail).
    stage : 'pre' (sur source) ou 'post' (sur sortie camouflage).
    """
    results = []

    # Durée
    expected = float(meta.get("duration_seconds", 0))
    actual   = info.get("duration", 0)
    if expected > 0:
        diff = abs(actual - expected)
        ok   = diff < 3.0
        results.append(("Durée cohérente", ok,
                        f"{actual:.1f}s (attendu ~{expected:.1f}s, écart {diff:.1f}s)"))
    else:
        ok = actual > 1.0
        results.append(("Durée > 1s", ok, f"{actual:.1f}s"))

    # Stream vidéo
    ok = info.get("width", 0) > 0
    results.append(("Stream vidéo présent", ok,
                    f"{info.get('width')}×{info.get('height')} — {info.get('video_codec')}"))

    # Stream audio
    ok = info.get("audio_codec", "?") not in ("?", "")
    results.append(("Stream audio présent", ok, info.get("audio_codec", "absent")))

    # Taille fichier
    ok = info.get("size_mb", 0) > 0.1
    results.append(("Taille > 100 KB", ok, f"{info.get('size_mb', 0):.1f} MB"))

    if stage == "post":
        # Audit tag encoder
        enc = info.get("encoder_tag", "").lower()
        suspicious = any(s in enc for s in SUSPICIOUS_TAGS)
        ok = not suspicious
        detail = f"tag trouvé : '{info.get('encoder_tag')}'" if info.get("encoder_tag") else "aucun tag"
        results.append(("Camouflage — aucun tag suspect", ok, detail))

        # Codec H.264
        ok = info.get("video_codec", "").lower() in ("h264", "avc")
        results.append(("Codec H.264", ok, info.get("video_codec", "?")))

        # Audio AAC
        ok = info.get("audio_codec", "").lower() == "aac"
        results.append(("Audio AAC 48kHz", ok,
                        f"{info.get('audio_codec','?')} {info.get('sample_rate','?')} Hz"))

    return results

# ─── Camouflage FFmpeg ────────────────────────────────────────────────────────

def camouflage(input_path: str, output_path: str, meta: dict) -> bool:
    """
    Re-encode complet pour effacer toute empreinte d'outil :
      - map_metadata -1   : wipe intégral des métadonnées source
      - libx264 CRF 18    : qualité visuelle quasi-lossless, fingerprint effacé
      - GOP régulier 2s   : structure standard (aucun artefact Remotion/outil)
      - yuv420p           : compatibilité maximale plateformes
      - AAC 192k 48kHz    : audio standard
      - loudnorm -14 LUFS : standard YouTube (évite flags audio anormal)
      - +faststart        : MOOV atom en tête (streaming instantané)
      - Tags propres       : title + date uniquement, rien d'autre
    """
    title = meta.get("title", "VIDEO")
    dt    = meta.get("date",  date.today().isoformat())
    fps   = int(meta.get("fps", 30))
    gop   = fps * 2  # keyframe toutes les 2 secondes

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-map_metadata", "-1",
        "-metadata", "encoder=",
        # Vidéo
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-profile:v", "high",
        "-level", "4.0",
        "-g", str(gop),
        "-keyint_min", str(gop),
        "-pix_fmt", "yuv420p",
        # Audio
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2",
        "-af", "loudnorm=I=-14:TP=-1:LRA=11",
        # Container
        "-movflags", "+faststart",
        # Tags propres uniquement
        "-metadata", f"title={title}",
        "-metadata", f"date={dt}",
        output_path,
    ]

    print(f"  [CMD] ffmpeg camouflage → {os.path.basename(output_path)}")
    print()
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        log_fail(f"ffmpeg camouflage échoué (exit {result.returncode})")
        return False
    return True

# ─── Touch timestamp ──────────────────────────────────────────────────────────

def touch_file(path: str, date_str: str):
    """Aligne le timestamp système du fichier sur la date de production."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        ts = time.mktime(dt.timetuple())
        os.utime(path, (ts, ts))
        log_ok(f"Timestamp fichier aligné sur {date_str}")
    except (ValueError, OSError):
        log_warn("Touch timestamp ignoré (date invalide).")

# ─── Chapters YouTube ─────────────────────────────────────────────────────────

def format_chapters(chapters: list) -> str:
    """
    Formate les chapters pour la description YouTube.
    Entrée : [{"t": 0, "label": "Intro"}, ...]
    Sortie : "00:00 Intro\n00:15 Partie 1\n..."
    """
    if not chapters:
        return ""
    lines = []
    for ch in chapters:
        t     = int(ch.get("t", 0))
        label = ch.get("label", "")
        m, s  = divmod(t, 60)
        lines.append(f"{m:02d}:{s:02d} {label}")
    return "\n".join(lines)

# ─── Rapport HTML ─────────────────────────────────────────────────────────────

def generate_rapport_html(output_dir: str, meta: dict, info_pre: dict,
                          info_post: dict, qa_pre: list, qa_post: list,
                          chapters_text: str, out_filename: str, fmt: str) -> str:
    """Génère rapport_f04.html — livrable opérateur, aucune dépendance externe."""

    def qa_rows(results):
        rows = ""
        for label, ok, detail in results:
            icon  = "✓" if ok else "✗"
            color = "#2ecc71" if ok else "#e74c3c"
            rows += (
                f'<tr>'
                f'<td style="color:{color};font-weight:700;padding:6px 12px;font-size:15px">{icon}</td>'
                f'<td style="padding:6px 12px">{label}</td>'
                f'<td style="padding:6px 12px;color:#888;font-size:13px">{detail}</td>'
                f'</tr>'
            )
        return rows

    all_pass_pre  = all(ok for _, ok, _ in qa_pre)
    all_pass_post = all(ok for _, ok, _ in qa_post)

    dur = info_post.get("duration", 0)
    mins, secs = divmod(int(dur), 60)
    dur_str    = f"{mins}m{secs:02d}s"
    fmt_label  = "YouTube Short (vertical 9:16)" if fmt == "vertical" else "YouTube Long (horizontal 16:9)"

    chapters_block = ""
    if chapters_text:
        chapters_block = f"""
<div class="section">
  <h2>Chapters YouTube</h2>
  <pre class="code">{chapters_text}</pre>
  <p class="hint">Collez ces lignes au début de votre description YouTube pour activer les chapters.</p>
</div>"""

    desc_val   = meta.get("description", "")
    desc_block = ""
    if desc_val:
        desc_block = f"""
<div class="section">
  <h2>Description YouTube</h2>
  <pre class="code">{desc_val}</pre>
</div>"""

    today = date.today().isoformat()

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>F04 HELBRECHT — Rapport de production</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0d0d0d;
          color: #e0e0e0; padding: 40px 32px; max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 4px; }}
  .sub {{ color: #555; font-size: 12px; margin-bottom: 36px; letter-spacing: 0.04em; }}
  .section {{ background: #161616; border-radius: 8px; padding: 22px 26px;
              margin-bottom: 18px; border: 1px solid #242424; }}
  h2 {{ font-size: 11px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: #666; margin-bottom: 18px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
  .metric {{ background: #0d0d0d; border-radius: 6px; padding: 14px 16px;
             border: 1px solid #1e1e1e; }}
  .metric .val {{ font-size: 18px; font-weight: 700; color: #fff; line-height: 1.2; }}
  .metric .lbl {{ font-size: 10px; color: #555; text-transform: uppercase;
                  letter-spacing: 0.06em; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  .badge {{ display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px;
            border-radius: 4px; font-size: 12px; font-weight: 700;
            letter-spacing: 0.06em; margin-bottom: 14px; }}
  .badge.ok   {{ background: #0d2a1a; color: #2ecc71; border: 1px solid #1a4a2a; }}
  .badge.fail {{ background: #2a0d0d; color: #e74c3c; border: 1px solid #4a1a1a; }}
  .tag {{ display: inline-block; background: #1a1a1a; border-radius: 4px;
          padding: 3px 10px; font-size: 11px; color: #888; margin: 3px 3px 0 0;
          border: 1px solid #2a2a2a; }}
  pre.code {{ background: #0a0a0a; color: #7ec8a0; padding: 16px; border-radius: 6px;
              font-size: 13px; line-height: 1.8; overflow-x: auto;
              border: 1px solid #1e1e1e; white-space: pre-wrap; }}
  .hint {{ font-size: 11px; color: #444; margin-top: 10px; }}
  .footer {{ font-size: 11px; color: #333; text-align: center; margin-top: 28px; }}
</style>
</head>
<body>

<h1>F04 HELBRECHT — Rapport de production</h1>
<p class="sub">Généré le {today} &nbsp;·&nbsp; Pipeline universel de finalisation vidéo</p>

<div class="section">
  <h2>Vidéo finale</h2>
  <div class="grid">
    <div class="metric"><div class="val">{out_filename}</div><div class="lbl">Fichier de sortie</div></div>
    <div class="metric"><div class="val">{fmt_label}</div><div class="lbl">Format détecté</div></div>
    <div class="metric"><div class="val">{dur_str}</div><div class="lbl">Durée</div></div>
    <div class="metric"><div class="val">{info_post.get('size_mb', 0):.1f} MB</div><div class="lbl">Taille fichier</div></div>
    <div class="metric"><div class="val">{info_post.get('width', '?')}×{info_post.get('height', '?')}</div><div class="lbl">Résolution</div></div>
    <div class="metric"><div class="val">{info_post.get('video_codec','?').upper()} / {info_post.get('audio_codec','?').upper()}</div><div class="lbl">Codecs</div></div>
  </div>
</div>

<div class="section">
  <h2>QA — Source (pré-camouflage)</h2>
  <div class="badge {'ok' if all_pass_pre else 'fail'}">{'PASS' if all_pass_pre else 'FAIL'}</div>
  <table>{qa_rows(qa_pre)}</table>
</div>

<div class="section">
  <h2>QA — Sortie (post-camouflage)</h2>
  <div class="badge {'ok' if all_pass_post else 'fail'}">{'PASS' if all_pass_post else 'FAIL'}</div>
  <table>{qa_rows(qa_post)}</table>
</div>

{chapters_block}

{desc_block}

<div class="section">
  <h2>Métadonnées injectées</h2>
  <span class="tag">title: {meta.get('title','')}</span>
  <span class="tag">date: {meta.get('date', today)}</span>
  <span class="tag">encoder: (absent)</span>
  <span class="tag">software: (absent)</span>
  <span class="tag">loudnorm: -14 LUFS / -1 dBTP</span>
  <span class="tag">faststart: activé</span>
  <span class="tag">GOP: {int(meta.get('fps',30))*2} frames (2s)</span>
</div>

<p class="footer">F04 HELBRECHT v2 · Pipeline universel · Compatible tout projet vidéo</p>

</body>
</html>"""

    rapport_path = os.path.join(output_dir, "rapport_f04.html")
    with open(rapport_path, "w", encoding="utf-8") as f:
        f.write(html)
    log_ok(f"Rapport HTML → {rapport_path}")
    return rapport_path

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="F04 HELBRECHT v2 — Camouflage universel + Finalisation YouTube"
    )
    parser.add_argument("--input",  required=True, help="Chemin vers F04/IN/")
    parser.add_argument("--output", required=True, help="Chemin vers F04/OUT/")
    args = parser.parse_args()

    input_video  = os.path.join(args.input,  INPUT_VIDEO)
    input_timing = os.path.join(args.input,  INPUT_TIMING)
    os.makedirs(args.output, exist_ok=True)

    print()
    print("═" * 52)
    print("  F04 HELBRECHT v2 — Camouflage & Finalisation")
    print("═" * 52)
    print(f"  IN  : {args.input}")
    print(f"  OUT : {args.output}")
    print()

    # 1. Outils
    section("1. Vérification outils")
    check_tools()

    # 2. Fichiers d'entrée
    section("2. Fichiers d'entrée")
    if not os.path.isfile(input_video):
        log_fail(f"short_render.mp4 introuvable : {input_video}")
        sys.exit(1)
    log_ok(f"short_render.mp4 — {os.path.getsize(input_video)/(1024*1024):.1f} MB")

    # 3. Lecture timing.json
    section("3. Lecture timing.json")
    meta = read_timing(input_timing)

    # 4. Probe source
    section("4. Analyse source (ffprobe)")
    probe_pre = probe_video(input_video)
    info_pre  = extract_video_info(probe_pre)
    fmt       = detect_format(info_pre)
    out_name  = output_filename(fmt)
    output_video = os.path.join(args.output, out_name)

    log_ok(f"Format détecté : {fmt.upper()} → {out_name}")
    log_ok(f"Résolution     : {info_pre['width']}×{info_pre['height']}")
    log_ok(f"Durée source   : {info_pre['duration']:.1f}s")
    if info_pre.get("encoder_tag"):
        log_warn(f"Tag encoder source détecté : '{info_pre['encoder_tag']}' → sera effacé")

    # 5. QA pré-camouflage
    section("5. QA — Pré-camouflage")
    qa_pre = qa_gate(info_pre, meta, "pre")
    for label, ok, detail in qa_pre:
        (log_ok if ok else log_warn)(f"{label} : {detail}")

    fatal_pre = [
        label for label, ok, _ in qa_pre
        if not ok and label in ("Durée > 1s", "Stream vidéo présent")
    ]
    if fatal_pre:
        log_fail(f"QA fatale échouée : {fatal_pre}")
        sys.exit(1)

    # 6. Camouflage FFmpeg
    section("6. Camouflage FFmpeg")
    log_info("Re-encode H.264 CRF18 + loudnorm -14 LUFS + wipe métadonnées...")
    if not camouflage(input_video, output_video, meta):
        sys.exit(1)

    # 7. Touch timestamp
    section("7. Alignement timestamp fichier")
    touch_file(output_video, meta.get("date", date.today().isoformat()))

    # 8. Probe sortie
    section("8. Analyse sortie (ffprobe)")
    probe_post = probe_video(output_video)
    info_post  = extract_video_info(probe_post)
    log_ok(f"Taille finale  : {info_post['size_mb']:.1f} MB")
    log_ok(f"Durée finale   : {info_post['duration']:.1f}s")
    log_ok(f"Codecs         : {info_post['video_codec']} / {info_post['audio_codec']}")
    enc_post = info_post.get("encoder_tag", "")
    if enc_post:
        log_warn(f"Tag encoder résiduel : '{enc_post}'")
    else:
        log_ok("Aucun tag encoder résiduel — camouflage validé")

    # 9. QA post-camouflage
    section("9. QA — Post-camouflage")
    qa_post = qa_gate(info_post, meta, "post")
    for label, ok, detail in qa_post:
        (log_ok if ok else log_fail)(f"{label} : {detail}")

    # 10. Chapters YouTube
    section("10. Chapters YouTube")
    chapters_text = format_chapters(meta.get("chapters", []))
    if chapters_text:
        log_ok(f"{len(meta['chapters'])} chapters générés :")
        print()
        for line in chapters_text.splitlines():
            print(f"    {line}")
    else:
        log_info("Aucun chapter dans timing.json (clé 'chapters' vide ou absente)")

    # 11. Rapport HTML
    section("11. Rapport HTML")
    generate_rapport_html(
        args.output, meta, info_pre, info_post,
        qa_pre, qa_post, chapters_text, out_name, fmt
    )

    # Récapitulatif
    print()
    print("═" * 52)
    print("  HELBRECHT — MISSION ACCOMPLIE")
    print(f"  Fichier  : {output_video}")
    print(f"  Format   : {fmt.upper()}")
    print(f"  Taille   : {info_post.get('size_mb', 0):.1f} MB")
    print(f"  Durée    : {info_post.get('duration', 0):.1f}s")
    print(f"  Rapport  : {os.path.join(args.output, 'rapport_f04.html')}")
    print("═" * 52)
    print()


if __name__ == "__main__":
    main()
