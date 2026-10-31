#!/usr/bin/env python3
"""Generate versioned public declarations; see docs/api/README.md for commands."""
import argparse
import json
import re
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--rust-json', type=Path, required=True)
p.add_argument('--check', action='store_true')
a = p.parse_args()
version = (ROOT/'VERSION').read_text().strip()
def go_doc(*args):
    return subprocess.check_output(['go','doc','-all',*args],cwd=ROOT/'go',text=True)
go = go_doc('.')
aliases = re.findall(r'^type (\w+) = (\w+)\.(\w+)',go,re.M)
expanded = {}
for public, module, target in aliases:
    expanded[public] = go_doc('./internal/'+module,target).strip()
chunks = re.split(r'(?=^type [A-Z]\w*)', go, flags=re.M)
blocks = ['## Functions and constants\n\n```go\n'+chunks[0].strip()+'\n```']
for chunk in chunks[1:]:
    name = re.match(r'type (\w+)', chunk)[1]
    content = chunk.strip()
    if name in expanded:
        content += '\n\n// Public alias: underlying declaration and methods.\n' + expanded[name]
    blocks.append('## '+name+'\n\n```go\n'+content+'\n```')
go_body = '\n\n'.join(blocks)+'\n'
d = json.loads(a.rust_json.read_text());index=d['index'];paths=d['paths']
if d['format_version'] != 45:
    raise SystemExit('Expected Rust 1.88 rustdoc JSON format 45; review generator before changing compiler.')
def item(n):return index[str(n)]
public_paths = {}
def walk(module_id, prefix):
    for child_id in item(module_id)['inner']['module']['items']:
        child = item(child_id)
        if child['visibility'] != 'public':
            continue
        if 'module' in child['inner']:
            walk(child_id, prefix + [child['name']])
        elif 'use' in child['inner']:
            use = child['inner']['use']
            target = use.get('id')
            if target is None or str(target) not in index:
                continue
            if use['is_glob'] and 'module' in item(target)['inner']:
                walk(target, prefix)
            else:
                public_paths[str(target)] = {'crate_id': 0, 'path': prefix + [use['name']]}
        else:
            public_paths[str(child_id)] = {'crate_id': 0, 'path': prefix + [child['name']]}
walk(d['root'], ['tuivory'])
def source(i):
    span=i.get('span')
    if not span:return ''
    lines=(ROOT/'rust'/span['filename']).read_text().splitlines()
    return '\n'.join(lines[span['begin'][0]-1:span['end'][0]]).strip()
entries=[]
for ident, meta in public_paths.items():
    i=index.get(ident)
    if not i or meta['crate_id']!=0 or i['visibility']!='public':continue
    kind=next(iter(i['inner']))
    if kind not in ('struct','enum','trait','type_alias','function','constant'):continue
    name='::'.join(meta['path']);s=source(i)
    if not s:continue
    if kind=='function':s=s.split('{',1)[0].rstrip()+';'
    if kind=='struct' and 'plain' in i['inner']['struct']['kind']:
        fields=i['inner']['struct']['kind']['plain']
        declarations=[source(item(n)) for n in fields['fields'] if item(n)['visibility']=='public']
        s=s.split('{',1)[0]+'{\n'+ '\n'.join('    '+x for x in declarations)
        if fields['has_stripped_fields']:s+='\n    // Private fields omitted.'
        s+='\n}'
    methods=[]
    for n in i['inner'][kind].get('impls',[]) if isinstance(i['inner'][kind],dict) else []:
        impl=item(n)['inner'].get('impl',{})
        if impl.get('trait') is not None:continue
        for mid in impl.get('items',[]):
            m=item(mid)
            if m['visibility']!='public' or 'function' not in m['inner']:continue
            sig=source(m).split('{',1)[0].rstrip()+';'
            note=m.get('docs') or ''
            if m.get('deprecation'):note+='\nDeprecated: '+str(m['deprecation'])
            methods.append('#### '+name+'::'+m['name']+'\n\n```rust\n'+sig+'\n```\n\n'+note+'\n')
    note=i.get('docs') or ''
    entries.append((name,'### '+name+'\n\n```rust\n'+s+'\n```\n\n'+note+'\n\n'+'\n'.join(methods)))
rust_body='\n'.join(body for name,body in sorted(entries))
for language, body in [('go',go_body),('rust',rust_body)]:
    for suffix in ['', '.en']:
        title=f'# {language.title()} API — {version}\n\n'
        intro=(f'**한국어 (기본)** · [English]({language}.en.md)\n\n[API 안내](README.md) · [컴포넌트 사용법](../components.md)\n\n실제 소스에서 생성한 공개 선언과 원문 주석입니다. 코드·심볼·원문 주석은 두 언어판에서 동일하게 유지합니다. 기본값·오류·이벤트 의미는 API 안내의 컴포넌트별 명세를 참고하세요. 외부 프레임워크의 상속/trait API는 해당 프레임워크 문서를 참고합니다.\n\n' if not suffix else f'[한국어 (default)]({language}.md) · **English**\n\n[API guide](README.en.md) · [Component guides](../components.en.md)\n\nGenerated public declarations and original source comments. Code, symbols and original comments are identical across language editions. See the API guide for component defaults, errors and event semantics. Inherited/trait APIs from external frameworks are documented by those frameworks.\n\n')
        result=title+intro+body
        target=ROOT/'docs/api'/f'{language}{suffix}.md'
        if a.check:
            if not target.exists() or target.read_text()!=result:raise SystemExit(f'Stale API reference: {target}')
        else:target.write_text(result)
print(f'Go root declarations + {len(aliases)} public aliases; Rust {len(entries)} public type/function entries and inherent methods: synchronized.')
