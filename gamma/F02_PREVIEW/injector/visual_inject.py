#!/usr/bin/env python3
"""
CRUSADER — Visual Injector v1
==============================

Curation des visuels du roadmap. Remplace les frames minables de F00.

Usage:
    # Générer le tableau de curation
    python visual_inject.py --roadmap roadmap.json --f00-dir /path/to/F00 --table

    # Appliquer des changements depuis un fichier de curation
    python visual_inject.py --roadmap roadmap.json --curation curation.json --apply

    # Vérifier les visuels (transparence, répétition, manquants)
    python visual_inject.py --roadmap roadmap.json --f00-dir /path/to/F00 --check

    # Redimensionner un upload externe → F00/RESERVE/
    python visual_inject.py --resize input.png --output F00_ASSET_FORGE/RESERVE/custom_001.png

L'injecteur:
  1. Lit le roadmap (82 segments)
  2. Génère un tableau de curation (chapitre, position, visuel, phrase, statut)
  3. Vérifie: transparence, répétition, fichier manquant, taille
  4. Applique les remplacements (upload PC ou pioche F00)
  5. Redimensionne les uploads à 1920x1080

L'injecteur NE MODIFIE JAMAIS:
  - start_frame, end_frame, text_subtitles (structure du roadmap)
  - crops, waypoints, fragments (travail manuel miniature)
  - style, meta, miniature chapters
"""

import json
import argparse
import os
import sys
from pathlib import Path
from collections import Counter

# === Détection des chapitres ===

def get_chapter_for_segment(seg_idx, chapters):
    """Retourne le chapitre auquel appartient un segment (0-indexed)."""
    for ch in chapters:
        start_seg = ch.get('start_segment', 0)
        # Trouver le chapitre suivant pour connaître la fin
        ch_idx = chapters.index(ch)
        if ch_idx + 1 < len(chapters):
            next_start = chapters[ch_idx + 1].get('start_segment', 999)
        else:
            next_start = 999
        
        # start_segment est 1-indexed dans le roadmap
        seg_num = seg_idx + 1
        if start_seg <= seg_num < next_start:
            return ch
    return None


# === Vérifications ===

def check_transparency(filepath):
    """Vérifie si un PNG a des pixels transparents (alpha=0)."""
    if not filepath.endswith('.png') or not os.path.exists(filepath):
        return None
    
    try:
        from PIL import Image
        img = Image.open(filepath)
        if img.mode != 'RGBA':
            return False  # Pas de canal alpha = pas transparent
        
        # Sampler: checker 1000 pixels aléatoires
        import random
        w, h = img.size
        transparent = 0
        samples = min(1000, w * h)
        for _ in range(samples):
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            r, g, b, a = img.getpixel((x, y))
            if a == 0:
                transparent += 1
        
        return transparent > 10  # Plus de 1% transparent
    except ImportError:
        return None  # PIL non disponible
    except Exception:
        return None


def check_file_exists(filepath, search_dirs):
    """Vérifie qu'un fichier existe dans un des dossiers de recherche."""
    for d in search_dirs:
        full = os.path.join(d, filepath)
        if os.path.exists(full):
            return full
    return None


def get_file_size(filepath):
    """Retourne (width, height) d'une image."""
    try:
        from PIL import Image
        img = Image.open(filepath)
        return img.size
    except:
        return None


# === Génération du tableau de curation ===

def generate_curation_table(roadmap, f00_dirs, check_transparency_flag=True):
    """
    Génère un tableau de curation pour tous les visuels du roadmap.
    """
    timeline = roadmap.get('timeline', [])
    chapters = roadmap.get('miniature', {}).get('chapters', [])
    
    table = []
    prev_file = None
    
    for i, entry in enumerate(timeline):
        image_file = entry.get('image_file', '')
        media_type = entry.get('media_type', 'image')
        text = entry.get('text_subtitles', '')[:80]
        
        # Chapitre
        ch = get_chapter_for_segment(i, chapters)
        ch_label = ch.get('label', '?') if ch else '?'
        ch_idx = chapters.index(ch) if ch else -1
        
        # Position dans le chapitre
        if ch:
            start_seg = ch.get('start_segment', 1)
            pos_in_chapter = (i + 1) - start_seg + 1
        else:
            pos_in_chapter = 0
        
        # Vérifications
        status = []
        flags = []
        
        # 1. Fichier existe?
        found_path = check_file_exists(image_file, f00_dirs)
        if not found_path:
            status.append('❌ MANQUANT')
            flags.append('missing')
        else:
            status.append('✅')
        
        # 2. Transparence
        if check_transparency_flag and found_path and image_file.endswith('.png'):
            is_transparent = check_transparency(found_path)
            if is_transparent:
                status.append('⚠️ TRANSPARENT')
                flags.append('transparent')
        
        # 3. Répétition
        if image_file == prev_file:
            status.append('⚠️ RÉPÉTITION')
            flags.append('repetition')
        prev_file = image_file
        
        # 4. Type match
        if image_file.endswith('.gif') and media_type != 'gif':
            status.append('⚠️ TYPE MISMATCH')
            flags.append('type_mismatch')
        elif image_file.endswith('.png') and media_type == 'gif':
            status.append('⚠️ TYPE MISMATCH')
            flags.append('type_mismatch')
        
        # 5. Premier visuel du chapitre = prioritaire
        is_first = pos_in_chapter == 1
        if is_first:
            flags.append('chapter_first')
        
        table.append({
            'segment_id': entry['id'],
            'chapter': ch_label,
            'chapter_idx': ch_idx,
            'position_in_chapter': pos_in_chapter,
            'is_chapter_first': is_first,
            'image_file': image_file,
            'media_type': media_type,
            'phrase': text,
            'status': ' | '.join(status) if status else '✅',
            'flags': flags,
            'action': 'keep',  # default
            'replacement': None,  # nouveau fichier si replace
            'replacement_source': None,  # 'upload' ou 'f00'
        })
    
    return table


# === Application des changements ===

def apply_curation(roadmap, curation_table):
    """
    Applique les changements du tableau de curation sur le roadmap.
    """
    timeline = roadmap.get('timeline', [])
    changes = []
    
    for entry in curation_table:
        if entry['action'] == 'keep':
            continue
        
        seg_id = entry['segment_id']
        replacement = entry.get('replacement')
        source = entry.get('replacement_source')
        
        if not replacement:
            continue
        
        # Trouver l'entrée dans le timeline
        for t_entry in timeline:
            if t_entry['id'] == seg_id:
                old_file = t_entry['image_file']
                t_entry['image_file'] = replacement
                
                # Mettre à jour media_type si nécessaire
                if replacement.endswith('.gif'):
                    t_entry['media_type'] = 'gif'
                else:
                    t_entry['media_type'] = 'image'
                
                changes.append({
                    'segment': seg_id,
                    'old': old_file,
                    'new': replacement,
                    'source': source
                })
                break
    
    return roadmap, changes


# === Redimensionnement ===

def resize_image(input_path, output_path, target_w=1920, target_h=1080):
    """
    Redimensionne une image à 1920x1080 avec crop center.
    Préserve le ratio, crop le centre.
    """
    from PIL import Image
    
    img = Image.open(input_path)
    
    # Convertir en RGB si RGBA (flatten sur noir)
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (0, 0, 0))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Calculer le crop center
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h
    
    if src_ratio > target_ratio:
        # Source plus large → crop horizontal
        new_w = int(src_h * target_ratio)
        offset = (src_w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, src_h))
    else:
        # Source plus haute → crop vertical
        new_h = int(src_w / target_ratio)
        offset = (src_h - new_h) // 2
        img = img.crop((0, offset, src_w, offset + new_h))
    
    # Resize final
    img = img.resize((target_w, target_h), Image.LANCZOS)
    
    # Sauvegarder
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, 'PNG', optimize=True)
    
    return output_path


# === Browse F00 ===

def browse_f00(f00_dir, media_type=None):
    """
    Liste tous les visuels disponibles dans F00.
    Retourne une liste de {filename, path, type, size, tags?}
    """
    results = []
    
    for root, dirs, files in os.walk(f00_dir):
        for fn in sorted(files):
            if fn.endswith('.png'):
                ft = 'image'
            elif fn.endswith('.gif'):
                ft = 'gif'
            else:
                continue
            
            if media_type and ft != media_type:
                continue
            
            full_path = os.path.join(root, fn)
            rel_path = os.path.relpath(full_path, f00_dir)
            
            # Taille
            try:
                from PIL import Image
                img = Image.open(full_path)
                w, h = img.size
                img.close()
            except:
                w, h = 0, 0
            
            # Transparence
            is_transparent = check_transparency(full_path) if ft == 'image' else False
            
            results.append({
                'filename': fn,
                'relative_path': rel_path,
                'type': ft,
                'width': w,
                'height': h,
                'transparent': is_transparent,
                'size_bytes': os.path.getsize(full_path),
            })
    
    return results


# === Main ===

def main():
    parser = argparse.ArgumentParser(description='CRUSADER Visual Injector v1')
    parser.add_argument('--roadmap', help='Path to roadmap.json')
    parser.add_argument('--f00-dir', help='Path to F00_ASSET_FORGE directory')
    parser.add_argument('--table', action='store_true', help='Generate curation table')
    parser.add_argument('--curation', help='Path to curation JSON to apply')
    parser.add_argument('--apply', action='store_true', help='Apply curation changes')
    parser.add_argument('--check', action='store_true', help='Check visuals only')
    parser.add_argument('--resize', help='Resize an image to 1920x1080')
    parser.add_argument('--output', help='Output path')
    parser.add_argument('--browse', action='store_true', help='Browse F00 available visuals')
    parser.add_argument('--media-type', help='Filter by media type (image/gif)')
    args = parser.parse_args()
    
    # === Mode: Resize ===
    if args.resize:
        if not args.output:
            print("❌ --output required with --resize")
            sys.exit(1)
        print(f"Redimensionnement: {args.resize} → {args.output}")
        resize_image(args.resize, args.output)
        print(f"✅ Image redimensionnée à 1920x1080: {args.output}")
        return
    
    # === Mode: Browse F00 ===
    if args.browse:
        if not args.f00_dir:
            print("❌ --f00-dir required with --browse")
            sys.exit(1)
        print("╔══════════════════════════════════════════════════════╗")
        print("║   CRUSADER — F00 Visual Browser                     ║")
        print("╚══════════════════════════════════════════════════════╝")
        print()
        visuals = browse_f00(args.f00_dir, args.media_type)
        print(f"Total: {len(visuals)} visuels")
        print(f"{'Filename':30s} {'Type':6s} {'Size':12s} {'Transparent':12s}")
        print("-" * 65)
        for v in visuals[:50]:
            transp = '⚠️ YES' if v['transparent'] else '✅ NO'
            print(f"{v['filename']:30s} {v['type']:6s} {v['width']}x{v['height']:6d}  {transp}")
        if len(visuals) > 50:
            print(f"  ... et {len(visuals) - 50} de plus")
        return
    
    # === Mode: Table / Check ===
    if args.table or args.check:
        if not args.roadmap:
            print("❌ --roadmap required")
            sys.exit(1)
        
        with open(args.roadmap, 'r') as f:
            roadmap = json.load(f)
        
        # Dirs de recherche pour les visuels
        f00_dirs = []
        if args.f00_dir:
            fire_dir = os.path.join(args.f00_dir, 'BANK_B_NATURE', 'fire')
            if os.path.exists(fire_dir):
                f00_dirs.append(fire_dir)
            reserve_dir = os.path.join(args.f00_dir, 'RESERVE')
            if os.path.exists(reserve_dir):
                f00_dirs.append(reserve_dir)
            f00_dirs.append(args.f00_dir)
        
        # Also check F03 public
        f03_public = os.path.join(os.path.dirname(args.roadmap), '..', '..', 'F03_SIGISMUND', 'CODEBASE', 'public')
        if os.path.exists(f03_public):
            f00_dirs.append(f03_public)
        
        print("╔══════════════════════════════════════════════════════╗")
        print("║   CRUSADER — Visual Curation Table                  ║")
        print("╚══════════════════════════════════════════════════════╝")
        print()
        
        table = generate_curation_table(roadmap, f00_dirs, check_transparency_flag=args.table)
        
        # Stats
        total = len(table)
        missing = sum(1 for t in table if 'missing' in t['flags'])
        transparent = sum(1 for t in table if 'transparent' in t['flags'])
        repetition = sum(1 for t in table if 'repetition' in t['flags'])
        chapter_firsts = sum(1 for t in table if t['is_chapter_first'])
        
        print(f"Total segments: {total}")
        print(f"Manquants: {missing}")
        print(f"Transparents: {transparent}")
        print(f"Répétitions: {repetition}")
        print(f"Premiers visuels de chapitre: {chapter_firsts}")
        print()
        
        # Print table
        print(f"{'Seg':>3s} {'Chapitre':20s} {'Pos':>3s} {'Visuel':25s} {'Type':5s} {'Statut':30s} {'Phrase'}")
        print("-" * 140)
        
        current_chapter = None
        for t in table:
            if t['chapter'] != current_chapter:
                current_chapter = t['chapter']
                print(f"  ── {current_chapter} {'─' * 120}")
            
            marker = '★' if t['is_chapter_first'] else ' '
            phrase = t['phrase'][:50]
            print(f"{marker}{t['segment_id']:3d} {t['chapter']:20s} {t['position_in_chapter']:3d} {t['image_file']:25s} {t['media_type']:5s} {t['status']:30s} {phrase}")
        
        if args.table:
            # Save table as JSON
            table_path = args.output or 'curation_table.json'
            with open(table_path, 'w') as f:
                json.dump(table, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Tableau sauvegardé: {table_path}")
            print(f"   Édite 'action' → 'replace' + 'replacement' → 'nom_du_fichier.png'")
            print(f"   Puis: python visual_inject.py --roadmap roadmap.json --curation {table_path} --apply")
        
        return
    
    # === Mode: Apply ===
    if args.apply:
        if not args.roadmap or not args.curation:
            print("❌ --roadmap and --curation required with --apply")
            sys.exit(1)
        
        with open(args.roadmap, 'r') as f:
            roadmap = json.load(f)
        
        with open(args.curation, 'r') as f:
            curation = json.load(f)
        
        print("╔══════════════════════════════════════════════════════╗")
        print("║   CRUSADER — Visual Injection                       ║")
        print("╚══════════════════════════════════════════════════════╝")
        print()
        
        corrected, changes = apply_curation(roadmap, curation)
        
        if changes:
            print(f"✅ {len(changes)} changement(s) appliqué(s):")
            for c in changes:
                print(f"  Seg {c['segment']}: {c['old']} → {c['new']} ({c['source']})")
        else:
            print("Aucun changement à appliquer.")
        
        output_path = args.output or args.roadmap
        with open(output_path, 'w') as f:
            json.dump(corrected, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Roadmap corrigé: {output_path}")
        
        return
    
    # No mode selected
    parser.print_help()


if __name__ == '__main__':
    main()
