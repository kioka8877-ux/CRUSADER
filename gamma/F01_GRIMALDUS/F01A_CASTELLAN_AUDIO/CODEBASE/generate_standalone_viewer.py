#!/usr/bin/env python3
"""
generate_standalone_viewer.py — Génère un viewer HTML standalone pour F01A
==========================================================================
Prend les données de l'API F01A (silences + waveform) et l'audio,
produit un HTML autonome exportable à l'opérateur.

Usage:
    1. Lancer crs_f01a.py en background:
       python crs_f01a.py --input ../IN --output ../OUT --port 5001 &

    2. Générer le viewer standalone:
       python generate_standalone_viewer.py --port 5001 --audio ../IN/audio_raw.mp3 --output viewer_standalone.html

    3. Exporter viewer_standalone.html à l'opérateur

L'opérateur écoute l'audio, coche/décoche les silences, clique VALIDATE,
puis copie le JSON dans le chat pour que l'agent traite.

Dépendances: requests (pip install requests)
"""

import argparse
import base64
import json
import os
import sys

try:
    import requests
except ImportError:
    print("[SETUP] pip install requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
    import requests


def fetch_api_data(port):
    """Récupère les données de l'API F01A."""
    base = f"http://localhost:{port}"
    analyze = requests.get(f"{base}/api/analyze").json()
    waveform = requests.get(f"{base}/api/waveform").json()
    return analyze, waveform


def encode_audio(audio_path):
    """Encode l'audio en base64."""
    with open(audio_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def generate_html(silences, peaks, duration, audio_b64):
    """Génère le HTML standalone du viewer."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>F01-A CASTELLAN-AUDIO — Silence Editor</title>
<style>
:root {{ --bg:#111;--surface:#1c1c1c;--border:#333;--gold:#c9a84c;--text:#ddd8cc;--text-dim:#888;--red:#e55;--green:#4caf50;--blue:#5b9bdf; }}
*{{ box-sizing:border-box;margin:0;padding:0; }}
body{{ background:var(--bg);color:var(--text);font-family:'Courier New',monospace;font-size:13px; }}
header{{ background:#0a0a0a;border-bottom:2px solid var(--gold);padding:12px 20px;display:flex;align-items:center;gap:16px; }}
header h1{{ font-size:14px;color:var(--gold);letter-spacing:3px;text-transform:uppercase; }}
header .info{{ color:var(--text-dim);font-size:11px;margin-left:auto; }}
.main{{ padding:20px;max-width:1200px;margin:0 auto; }}
.waveform-container{{ background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:10px;margin:16px 0;position:relative;cursor:pointer; }}
canvas#waveform{{ width:100%;height:150px;display:block; }}
.controls{{ display:flex;gap:10px;align-items:center;margin:12px 0;flex-wrap:wrap; }}
.controls button{{ background:var(--surface);border:1px solid var(--border);color:var(--text);padding:8px 16px;border-radius:4px;cursor:pointer;font-family:inherit;font-size:12px; }}
.controls button:hover{{ border-color:var(--gold);color:var(--gold); }}
.time-display{{ font-size:18px;color:var(--gold);font-weight:bold;min-width:120px;text-align:center; }}
.silence-list{{ background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:16px;margin:16px 0; }}
.silence-list h3{{ color:var(--gold);font-size:12px;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px; }}
.silence-item{{ display:flex;align-items:center;gap:12px;padding:8px 12px;border-bottom:1px solid var(--border);font-size:12px; }}
.silence-item:last-child{{ border-bottom:none; }}
.silence-item .idx{{ color:var(--text-dim);min-width:30px; }}
.silence-item .times{{ color:var(--blue);min-width:200px; }}
.silence-item .dur{{ color:var(--text-dim);min-width:80px; }}
.silence-item label{{ display:flex;align-items:center;gap:6px;cursor:pointer; }}
.silence-item input[type="checkbox"]{{ accent-color:var(--red);width:16px;height:16px; }}
.silence-item .remove-label{{ color:var(--red); }}
.silence-item button{{ background:none;border:1px solid var(--border);color:var(--text-dim);padding:4px 8px;border-radius:3px;cursor:pointer;font-family:inherit;font-size:11px; }}
.silence-item button:hover{{ border-color:var(--gold);color:var(--gold); }}
.summary{{ background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:16px;margin:16px 0;display:flex;gap:30px;flex-wrap:wrap; }}
.summary .stat{{ display:flex;flex-direction:column;gap:4px; }}
.summary .stat .label{{ font-size:10px;color:var(--text-dim);text-transform:uppercase;letter-spacing:1px; }}
.summary .stat .value{{ font-size:16px;color:var(--gold);font-weight:bold; }}
.validate-section{{ margin:20px 0;text-align:center; }}
.validate-section button{{ background:var(--green);color:#fff;border:none;padding:14px 40px;font-size:14px;font-family:inherit;border-radius:4px;cursor:pointer;letter-spacing:1px;text-transform:uppercase; }}
.validate-section button:hover{{ background:#3bc43b; }}
.validate-section button:disabled{{ background:var(--border);color:var(--text-dim);cursor:not-allowed; }}
#result{{ display:none;background:var(--surface);border:2px solid var(--green);border-radius:4px;padding:20px;margin:20px 0;text-align:center; }}
#result h3{{ color:var(--green);margin-bottom:10px; }}
</style>
</head>
<body>
<header>
  <h1>F01-A CASTELLAN-AUDIO</h1>
  <span class="info">Silence Editor — Operator Decision</span>
</header>
<div class="main">
  <div class="summary">
    <div class="stat"><span class="label">Duration</span><span class="value">{duration:.1f}s ({duration/60:.1f} min)</span></div>
    <div class="stat"><span class="label">Silences Detected</span><span class="value">{len(silences)}</span></div>
    <div class="stat"><span class="label">Total Silence</span><span class="value">{sum(s["duration"] for s in silences):.2f}s</span></div>
    <div class="stat"><span class="label">After Removal</span><span class="value" id="dur-after">—</span></div>
  </div>
  <div class="waveform-container" id="waveform-container"><canvas id="waveform"></canvas></div>
  <div class="controls">
    <button id="btn-play" onclick="togglePlay()">▶ Play</button>
    <span class="time-display" id="time-display">0:00 / {int(duration)//60}:{int(duration)%60:02d}</span>
    <button onclick="selectAll(true)">Select All Silences</button>
    <button onclick="selectAll(false)">Deselect All</button>
  </div>
  <div class="silence-list">
    <h3>Silences Detected (check = REMOVE)</h3>
    <div id="silence-items"></div>
  </div>
  <div class="validate-section">
    <button id="btn-validate" onclick="validate()">✅ VALIDATE — Record Decision</button>
  </div>
  <div id="result"><h3>✅ Decision Recorded</h3><p id="result-text"></p></div>
</div>
<script>
const SILENCES={json.dumps(silences)};
const PEAKS={json.dumps(peaks)};
const DURATION={duration};
let audio=null,playing=false;
function initAudio(){{ audio=new Audio("data:audio/mpeg;base64,"+"{audio_b64}"); audio.addEventListener('ended',()=>{{ playing=false;document.getElementById('btn-play').textContent='▶ Play'; }}); }}
function drawWaveform(){{
  const c=document.getElementById('waveform'),ctx=c.getContext('2d'),dpr=window.devicePixelRatio||1,r=c.getBoundingClientRect();
  c.width=r.width*dpr;c.height=r.height*dpr;ctx.scale(dpr,dpr);
  const W=r.width,H=r.height,mid=H/2;
  ctx.fillStyle='#1c1c1c';ctx.fillRect(0,0,W,H);
  SILENCES.forEach((s,i)=>{{const cb=document.getElementById('sil-'+i);const x1=(s.start/DURATION)*W,x2=(s.end/DURATION)*W;ctx.fillStyle=cb&&cb.checked?'rgba(229,85,85,0.3)':'rgba(74,74,74,0.2)';ctx.fillRect(x1,0,x2-x1,H);}});
  const bw=W/PEAKS.length;
  PEAKS.forEach((p,i)=>{{const bh=p*mid*0.9,x=i*bw;ctx.fillStyle='#5b9bdf';ctx.fillRect(x,mid-bh,Math.max(bw-1,1),bh*2);}});
  if(audio){{const px=(audio.currentTime/DURATION)*W;ctx.strokeStyle='#c9a84c';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(px,0);ctx.lineTo(px,H);ctx.stroke();}}
}}
function updateTime(){{ const t=audio?audio.currentTime:0;const m=Math.floor(t/60),s=Math.floor(t%60);const tm=Math.floor(DURATION/60),ts=Math.floor(DURATION%60);document.getElementById('time-display').textContent=m+':'+String(s).padStart(2,'0')+' / '+tm+':'+String(ts).padStart(2,'0');drawWaveform(); }}
function togglePlay(){{ if(!audio)initAudio();if(playing){{audio.pause();playing=false;document.getElementById('btn-play').textContent='▶ Play';}}else{{audio.play();playing=true;document.getElementById('btn-play').textContent='⏸ Pause';(function anim(){{if(!playing)return;updateTime();requestAnimationFrame(anim);}})();}} }}
document.getElementById('waveform-container').addEventListener('click',(e)=>{{if(!audio)initAudio();const r=e.currentTarget.getBoundingClientRect();audio.currentTime=((e.clientX-r.left)/r.width)*DURATION;updateTime();}});
function buildSilenceList(){{
  const c=document.getElementById('silence-items');c.innerHTML='';
  SILENCES.forEach((s,i)=>{{const d=document.createElement('div');d.className='silence-item';
  const sm=Math.floor(s.start/60),ss=Math.floor(s.start%60),em=Math.floor(s.end/60),es=Math.floor(s.end%60);
  d.innerHTML=`<span class="idx">#${{i+1}}</span><span class="times">${{sm}}:${{String(ss).padStart(2,'0')}} → ${{em}}:${{String(es).padStart(2,'0')}}</span><span class="dur">${{s.duration.toFixed(2)}}s</span><label><input type="checkbox" id="sil-${{i}}" checked onchange="updateSummary();drawWaveform()"><span class="remove-label">Remove</span></label><button onclick="playSil(${{i}})">▶ Listen</button>`;
  c.appendChild(d);}});updateSummary();
}}
function playSil(i){{ if(!audio)initAudio();audio.currentTime=Math.max(0,SILENCES[i].start-2);audio.play();playing=true;document.getElementById('btn-play').textContent='⏸ Pause';(function a(){{if(!playing)return;updateTime();requestAnimationFrame(a);}})();setTimeout(()=>{{audio.pause();playing=false;document.getElementById('btn-play').textContent='▶ Play';}},((SILENCES[i].duration+4)*1000)); }}
function selectAll(v){{ SILENCES.forEach((_,i)=>{{document.getElementById('sil-'+i).checked=v;}});updateSummary();drawWaveform(); }}
function updateSummary(){{ let r=0;SILENCES.forEach((s,i)=>{{if(document.getElementById('sil-'+i).checked)r+=s.duration;}});document.getElementById('dur-after').textContent=(DURATION-r).toFixed(1)+'s ('+ ((DURATION-r)/60).toFixed(1)+' min)'; }}
function validate(){{
  const rm=[];SILENCES.forEach((s,i)=>{{if(document.getElementById('sil-'+i).checked)rm.push(s);}});
  const dec={{silences_to_remove:rm,silences_to_keep:SILENCES.filter((_,i)=>!document.getElementById('sil-'+i).checked),original_duration:DURATION,removed_count:rm.length,total_removed_seconds:rm.reduce((a,s)=>a+s.duration,0)}};
  document.getElementById('result').style.display='block';
  document.getElementById('result-text').innerHTML='<strong>'+rm.length+' silence(s) marked for removal</strong><br>Total removed: '+dec.total_removed_seconds.toFixed(2)+'s<br>Final duration: '+(DURATION-dec.total_removed_seconds).toFixed(1)+'s<br><br><textarea style="width:100%;height:150px;background:#111;color:#ddd;border:1px solid #333;font-family:monospace;font-size:11px;padding:8px;" readonly>'+JSON.stringify(dec,null,2)+'</textarea><br><br><strong style="color:#c9a84c;">Copy the JSON above and paste it in the chat to proceed.</strong>';
  document.getElementById('btn-validate').disabled=true;document.getElementById('btn-validate').textContent='✅ Decision Recorded';
}}
window.addEventListener('load',()=>{{buildSilenceList();drawWaveform();}});
window.addEventListener('resize',drawWaveform);
</script>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate standalone F01A silence editor viewer")
    parser.add_argument("--port", type=int, default=5001, help="Port of running crs_f01a.py server")
    parser.add_argument("--audio", required=True, help="Path to audio_raw.mp3")
    parser.add_argument("--output", default="viewer_standalone.html", help="Output HTML file")
    args = parser.parse_args()

    print(f"[F01A] Fetching API data from localhost:{args.port}...")
    analyze, waveform = fetch_api_data(args.port)

    print(f"[F01A] Encoding audio: {args.audio}")
    audio_b64 = encode_audio(args.audio)

    silences = analyze.get('silences', [])
    peaks = waveform.get('peaks', [])
    duration = waveform.get('duration', 0)

    print(f"[F01A] Duration: {duration:.1f}s | Silences: {len(silences)} | Peaks: {len(peaks)}")

    html = generate_html(silences, peaks, duration, audio_b64)

    with open(args.output, 'w') as f:
        f.write(html)

    size_mb = os.path.getsize(args.output) / 1024 / 1024
    print(f"[F01A] ✅ Viewer written: {args.output} ({size_mb:.1f} MB)")
    print(f"[F01A] Export this HTML to the operator for silence validation.")


if __name__ == "__main__":
    main()
