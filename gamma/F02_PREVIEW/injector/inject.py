#!/usr/bin/env python3
"""
CRUSADER — Roadmap Injector v1
================================

Valide et corrige un roadmap.json exporté par F02 pour qu'il respecte
le contrat announce-sync (miniature = pendant l'annonce du nom, pas silence).

Usage:
    python inject.py --roadmap path/to/roadmap.json --timing path/to/timing.json [--output corrected.json] [--dry-run]

L'injecteur:
  1. Lit timing.json (source de vérité: audio + Whisper)
  2. Lit roadmap.json (export F02)
  3. Valide chaque règle de rules.json
  4. Injecte les champs manquants (announce frames, labels, text_subtitles)
  5. PRÉSERVE les crops/waypoints/fragments manuels
  6. Émet un rapport de validation

L'injecteur NE MODIFIE JAMAIS:
  - crops, waypoints, fragments, imageURLs (travail manuel de l'opérateur)
  - style (choix visuels)
  - timeline (structure des segments)
"""

import json
import argparse
import re
import sys
from pathlib import Path


# === Détection des annonces dans timing.json ===

def find_announce_in_timing(timing, chapter_name):
    """
    Trouve la fenêtre d'annonce d'un chapitre dans timing.json.
    
    Stratégie:
    1. Chercher un segment dont le texte = le nom du chapitre (ou commence par)
    2. Si trouvé, utiliser les word-level frames pour affiner
    3. Retourner (start_frame, end_frame, segment_id)
    """
    segments = timing.get('segments', [])
    name_lower = chapter_name.lower().strip()
    
    # Étape 1: chercher un segment qui est juste le nom (court, ~1-2s)
    best_match = None
    best_score = -1
    
    for seg in segments:
        text = seg['text'].lower().strip()
        text_clean = re.sub(r'[.,!?;:]$', '', text).strip()
        
        # Match exact (le segment = juste le nom)
        if text_clean == name_lower:
            return seg['start_frame'], seg['end_frame'], seg['id']
        
        # Match: le segment commence par le nom
        if text_clean.startswith(name_lower):
            # Score = proximité (plus le segment est court, mieux c'est)
            duration = seg['end_frame'] - seg['start_frame']
            score = 1000 - duration  # court = meilleur
            if score > best_score:
                best_score = score
                best_match = seg
    
    # Étape 2: si on a un match "commence par", affiner avec les mots
    if best_match:
        # Trouver les mots qui correspondent au nom du chapitre
        words = best_match.get('words', [])
        name_words = name_lower.split()
        
        # Trouver le premier mot du nom
        start_frame = best_match['start_frame']
        end_frame = best_match['end_frame']
        
        if words and len(name_words) > 0:
            # Chercher la séquence de mots qui correspond au nom
            for i, w in enumerate(words):
                if w['word'].lower().strip().strip('.,!?;:') == name_words[0]:
                    # Vérifier si les mots suivants correspondent
                    match = True
                    end_idx = i
                    for j, nw in enumerate(name_words):
                        if i + j >= len(words):
                            match = False
                            break
                        if words[i + j]['word'].lower().strip().strip('.,!?;:') != nw:
                            match = False
                            break
                        end_idx = i + j
                    
                    if match:
                        start_frame = words[i]['start_frame']
                        end_frame = words[end_idx]['end_frame']
                        break
        
        return start_frame, end_frame, best_match['id']
    
    # Étape 3: fallback — chercher dans tous les segments le premier mot du nom
    name_words = name_lower.split()
    first_word = name_words[0] if name_words else name_lower
    for seg in segments:
        words = seg.get('words', [])
        for w in words:
            if w['word'].lower().strip().strip('.,!?;:') == first_word:
                return w['start_frame'], w.get('end_frame', seg['end_frame']), seg['id']
    
    return None, None, None


def detect_chapter_count(timing):
    """
    Détecte combien d'annonces de chapitre existent dans le script.
    Cherche les 8 noms connus + variants.
    """
    known_names = [
        "tropical storm",
        "category 1 hurricane",
        "category 3 hurricane",
        "category 5",
        "super typhoon",
        "cyclone",
        "bomb cyclone",
        "hypercane"
    ]
    
    found = []
    for name in known_names:
        start, end, seg_id = find_announce_in_timing(timing, name)
        if start is not None:
            found.append({
                'name': name,
                'announce_start_frame': start,
                'announce_end_frame': end,
                'segment_id': seg_id
            })
    
    return found


# === Validation et injection ===

def validate_and_inject(roadmap, timing, rules, dry_run=False):
    """
    Valide un roadmap contre les règles et injecte les champs manquants.
    Retourne (corrected_roadmap, report).
    """
    report = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'injections': [],
        'preserved': []
    }
    
    segments = timing.get('segments', [])
    
    # === Règle: timeline_count ===
    timeline = roadmap.get('timeline', [])
    if len(timeline) != len(segments):
        report['warnings'].append(
            f"timeline_count: {len(timeline)} segments vs timing.json {len(segments)} — mismatch"
        )
    
    # === Règle: text_subtitles ===
    missing_text = 0
    for i, entry in enumerate(timeline):
        if 'text_subtitles' not in entry or not entry['text_subtitles']:
            if i < len(segments):
                entry['text_subtitles'] = segments[i]['text']
                missing_text += 1
                report['injections'].append(
                    f"text_subtitles: seg {entry['id']} — injected from timing.json"
                )
    
    if missing_text > 0:
        report['warnings'].append(f"text_subtitles: {missing_text} entries were missing, injected from timing.json")
    
    # === Règle: chapter_count ===
    mini = roadmap.get('miniature', {})
    chapters = mini.get('chapters', [])
    
    detected = detect_chapter_count(timing)
    if len(chapters) != len(detected):
        report['warnings'].append(
            f"chapter_count: roadmap has {len(chapters)} chapters, script announces {len(detected)}"
        )
    
    # === Règle: announce_frames + labels + start_segment ===
    for i, ch in enumerate(chapters):
        # Préserver les champs manuels
        preserved_fields = ['crop', 'waypoints', 'fragment', 'imageURL', 'isDiagonal']
        for pf in preserved_fields:
            if pf in ch:
                report['preserved'].append(f"ch[{i}].{pf} — preserved (manual)")
        
        # Injecter announce frames si manquants
        if ch.get('announce_start_frame') is None or ch.get('announce_end_frame') is None:
            # Déterminer le nom du chapitre
            # Si le label est générique ("Chapitre N"), utiliser le nom détecté
            label = ch.get('label', '')
            is_generic = re.match(r'^[Cc]hapitre\s+\d+', label) or not label
            
            if is_generic and i < len(detected):
                chapter_name = detected[i]['name']
                announce_start = detected[i]['announce_start_frame']
                announce_end = detected[i]['announce_end_frame']
                seg_id = detected[i]['segment_id']
            else:
                # Utiliser le label existant pour chercher
                announce_start, announce_end, seg_id = find_announce_in_timing(timing, label)
                chapter_name = label
            
            if announce_start is not None and announce_end is not None:
                ch['announce_start_frame'] = announce_start
                ch['announce_end_frame'] = announce_end
                ch['announce_start'] = round(announce_start / timing['meta']['fps'], 2)
                ch['announce_end'] = round(announce_end / timing['meta']['fps'], 2)
                report['injections'].append(
                    f"ch[{i}].announce_frames: {announce_start}-{announce_end} ({chapter_name})"
                )
            else:
                report['errors'].append(
                    f"ch[{i}]: impossible de trouver l'annonce pour '{chapter_name}' dans timing.json"
                )
                report['valid'] = False
        
        # Injecter le label si générique
        label = ch.get('label', '')
        is_generic = re.match(r'^[Cc]hapitre\s+\d+', label) or not label
        if is_generic and i < len(detected):
            old_label = label
            # Capitaliser proprement
            new_label = detected[i]['name'].title()
            if 'category' in new_label.lower():
                new_label = new_label.replace('Category', 'Category')
            ch['label'] = new_label
            report['injections'].append(
                f"ch[{i}].label: '{old_label}' → '{new_label}'"
            )
        
        # Corriger start_segment si nécessaire
        if i < len(detected):
            correct_seg = detected[i]['segment_id'] + 1  # timing segs are 0-indexed, roadmap is 1-indexed
            current_seg = ch.get('start_segment')
            if current_seg != correct_seg:
                old_seg = current_seg
                ch['start_segment'] = correct_seg
                report['injections'].append(
                    f"ch[{i}].start_segment: {old_seg} → {correct_seg}"
                )
    
    # === Mettre à jour remap_meta ===
    if 'remap_meta' not in roadmap:
        roadmap['remap_meta'] = {}
    roadmap['remap_meta']['injector_version'] = '1.0'
    roadmap['remap_meta']['injected_at'] = 'auto'
    roadmap['remap_meta']['engine_touched'] = False
    roadmap['remap_meta']['crops_source'] = 'user manual via F02 MiniatureEditor'
    
    return roadmap, report


# === Main ===

def main():
    parser = argparse.ArgumentParser(description='CRUSADER Roadmap Injector v1')
    parser.add_argument('--roadmap', required=True, help='Path to roadmap.json')
    parser.add_argument('--timing', required=True, help='Path to timing.json')
    parser.add_argument('--output', default=None, help='Output path (default: overwrite input)')
    parser.add_argument('--dry-run', action='store_true', help='Validate only, no output')
    args = parser.parse_args()
    
    # Load files
    with open(args.timing, 'r') as f:
        timing = json.load(f)
    
    with open(args.roadmap, 'r') as f:
        roadmap = json.load(f)
    
    # Load rules
    rules_path = Path(__file__).parent / 'rules.json'
    with open(rules_path, 'r') as f:
        rules = json.load(f)
    
    print("╔══════════════════════════════════════════════════════╗")
    print("║   CRUSADER — Roadmap Injector v1                     ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    
    # Run
    corrected, report = validate_and_inject(roadmap, timing, rules, dry_run=args.dry_run)
    
    # Print report
    print(f"Source de vérité: {args.timing}")
    print(f"Roadmap: {args.roadmap}")
    print(f"Timeline segments: {len(roadmap.get('timeline', []))}")
    print(f"Timing segments: {len(timing.get('segments', []))}")
    print(f"Miniature chapters: {len(roadmap.get('miniature', {}).get('chapters', []))}")
    print()
    
    detected = detect_chapter_count(timing)
    print(f"Annonces détectées dans le script: {len(detected)}")
    for d in detected:
        print(f"  {d['name']:30s} → frames {d['announce_start_frame']:5d}-{d['announce_end_frame']:5d} (seg {d['segment_id']})")
    print()
    
    if report['errors']:
        print(f"❌ ERREURS ({len(report['errors'])}):")
        for e in report['errors']:
            print(f"  • {e}")
    
    if report['warnings']:
        print(f"⚠️  WARNINGS ({len(report['warnings'])}):")
        for w in report['warnings']:
            print(f"  • {w}")
    
    if report['injections']:
        print(f"✅ INJECTIONS ({len(report['injections'])}):")
        for inj in report['injections']:
            print(f"  • {inj}")
    
    if report['preserved']:
        print(f"🔒 PRÉSERVÉ ({len(report['preserved'])} champs manuels):")
        print(f"  • crops, waypoints, fragments, imageURLs — NON touchés")
    
    print()
    print(f"VERDICT: {'✅ VALIDE' if report['valid'] else '❌ INVALIDE'}")
    
    if not args.dry_run and report['valid']:
        output_path = args.output or args.roadmap
        with open(output_path, 'w') as f:
            json.dump(corrected, f, indent=2)
        print(f"\n📄 Roadmap corrigé écrit: {output_path}")
    elif args.dry_run:
        print(f"\n🔍 Dry-run — aucun fichier écrit")


if __name__ == '__main__':
    main()
