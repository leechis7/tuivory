#!/usr/bin/env python3
"""Embed shared palette and Unicode data in independent language packages."""
from pathlib import Path
import json
import argparse
ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()

def emit(path, content):
    if args.check:
        if not path.exists() or path.read_text() != content:
            raise SystemExit(f"Stale independent-language data: {path.relative_to(ROOT)}")
    else:
        path.write_text(content)

def generate():
    fold=json.loads((ROOT/'design/casefold.json').read_text())
    for path in ['python/src/tuivory/casefold.json','javascript/src/casefold.json']:
        emit(ROOT/path,json.dumps(fold,ensure_ascii=False,separators=(',',':'))+'\n')
    pairs=sorted((int(k),v)for k,v in fold['mappings'].items())
    native='/* Generated Unicode17 default full case folding. See CASEFOLD-LICENSE. */\nstatic const struct { unsigned cp; const char *text; } tui_fold_data[] = {'+','.join('{'+str(cp)+','+json.dumps(value,ensure_ascii=False)+'}'for cp,value in pairs)+'};\n'
    for language in ['c','cpp']:emit(ROOT/f'{language}/include/tuivory_fold.h',native)
    java='package io.tuivory;\n// Generated Unicode17 C+F mappings. See CASEFOLD-LICENSE.\nfinal class FoldData {\nstatic final int[] KEYS={'+','.join(str(cp)for cp,_ in pairs)+'};\nstatic final String[] VALUES={'+','.join(json.dumps(v,ensure_ascii=True)for _,v in pairs)+'};\nprivate FoldData(){}\n}\n'
    emit(ROOT/'java/src/main/java/io/tuivory/FoldData.java',java)
    linear=[]
    for n in range(256):
        v=n/255
        linear.append(format(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4,'.17g'))
    tokens = json.loads((ROOT/'design/tokens/candidate.json').read_text())
    width = json.loads((ROOT/'design/unicode-width.json').read_text())
    for path in ['python/src/tuivory/tokens.json','javascript/src/tokens.json']:
        emit(ROOT/path, json.dumps(tokens, ensure_ascii=False, indent=2)+'\n')
    emit(ROOT/'javascript/src/unicode-width.json', json.dumps(width,separators=(',',':'))+'\n')
    gcb = json.loads((ROOT/'design/grapheme-properties.json').read_text())['properties']
    for lang in ['c','cpp']:
        lines=['/* Generated from design/ data. Unicode ranges: wcwidth MIT, see NOTICE. */']
        lines.append('static const double tui_luminance[] = {'+','.join(linear)+'};')
        for name in ['wide','zero','vs15','vs16','pictographic','virama','spacing_mc']:
            ranges=','.join('{'+str(a)+','+str(b)+'}' for a,b in width[name])
            lines.append(f'static const unsigned int tui_{name}[][2] = {{{ranges}}};')
        for name, values in gcb.items():
            ranges=','.join('{'+str(a)+','+str(b)+'}' for a,b in values)
            lines.append(f'static const unsigned int tui_{name.lower()}[][2] = {{{ranges}}};')
        # Role and theme ordering are public, fixed by the common token source.
        lines.append('static const char *const tui_roles[] = {'+','.join(json.dumps(r) for r in tokens['roles'])+'};')
        entries=[]
        for theme in ['dark','light','blackwhite']:
            for profile in ['8','16','256','truecolor']:
                for role in tokens['roles']:
                    t=tokens['palettes'][theme+'-'+profile][role]
                    def color(s):return int(s[1:],16)|0x1000000 if s.startswith('#') else int(s)
                    entries.append('{'+','.join(map(str,[color(t['foreground']),color(t['background']),int(t['fontWeight']=='bold')]))+'}')
        lines.append('static const unsigned int tui_palette_data[][3] = {'+','.join(entries)+'};')
        emit(ROOT/f'{lang}/include/tuivory_data.h', '\n'.join(lines)+'\n')
    lines=['package io.tuivory;','// Generated common data; wcwidth MIT attribution in NOTICE.','final class Data {']
    for name in ['wide','zero','vs15','vs16','pictographic','virama','spacing_mc']:
        lines.append(f'static final int[][] {name.upper()} = {{'+','.join('{'+str(a)+','+str(b)+'}'for a,b in width[name])+'};')
    lines.append('static final double[] LUMINANCE = {'+','.join(linear)+'};')
    lines.append('static final String[] ROLES = {'+','.join(json.dumps(r)for r in tokens['roles'])+'};')
    lines.append('static final int[][] PALETTES = {'+','.join(entries)+'};')
    lines.append('private Data() {}\n}')
    emit(ROOT/'java/src/main/java/io/tuivory/Data.java', '\n'.join(lines)+'\n')
if __name__ == '__main__': generate()
