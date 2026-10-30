#!/usr/bin/env python3
"""Check explicit API deprecation exceptions against source and paired guides.

This checks the declaration forms used by this repository, not arbitrary Rust/Go
syntax. Unknown deprecation declaration forms fail instead of being ignored.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def annotations(root):
    found = {}
    errors = []
    for path in (root / 'rust' / 'src').rglob('*.rs'):
        text = path.read_text()
        for attr in re.finditer(r'(?m)^\s*#\[deprecated(?:\((.*?)\))?\]', text, re.S):
            declaration = re.match(r'\s*pub\s+(?:fn\s+)?(\w+)\s*[:(<]', text[attr.end():])
            owners = list(re.finditer(r'pub struct\s+(\w+)|impl(?:<[^>]+>)?\s+(\w+)', text[:attr.start()]))
            if not declaration or not owners:
                errors.append(f'{path.relative_to(root)}: unsupported deprecated declaration')
                continue
            owner = next(x for x in owners[-1].groups() if x)
            key = (str(path.relative_to(root)), owner, declaration[1])
            if key in found:
                errors.append(f'duplicate source annotation: {key}')
            found[key] = attr[1] or ''
    for path in (root / 'go').rglob('*.go'):
        if path.name.endswith('_test.go'):
            continue
        text = path.read_text()
        for match in re.finditer(r'(?m)^\s*// Deprecated:\s*([^\n]+)', text):
            after = text[match.end():]
            declaration = re.match(r'(?:\s*//[^\n]*)*\s*(?:func\s+(?P<receiver>\([^)]*\)\s+)?|type\s+)(?P<name>[A-Z]\w*)', after)
            if not declaration:
                field = re.match(r'(?:\s*//[^\n]*)*\s*([A-Z]\w*)\s+[^\n]+', after)
                owner_match = re.search(r'type\s+(\w+)\s+struct\s*\{[^}]*$', text[:match.start()], re.S)
                if field and owner_match:
                    found[(str(path.relative_to(root)), owner_match[1], field[1])] = match[1]
                else:
                    errors.append(f'{path.relative_to(root)}: unsupported Go Deprecated declaration')
                continue
            receiver = re.search(r'\(\w+\s+\*?(\w+)', declaration['receiver'] or '')
            owner = receiver[1] if receiver else ''
            found[(str(path.relative_to(root)), owner, declaration['name'])] = match[1]
    return found, errors


def inspect(root=ROOT):
    data = json.loads((root / 'design/api-lifecycle.json').read_text())
    if data.get('format') != 'tuivory.api-lifecycle.v1':
        return ['unknown lifecycle format']
    source, errors = annotations(root)
    docs = {lang: (root / f'docs/api-lifecycle{lang}.md').read_text() for lang in ['', '.en']}
    expected = set()
    ids = set()
    for entry in data['entries']:
        api = entry['api']
        if api in ids:
            errors.append(f'duplicate API: {api}')
        ids.add(api)
        key = (entry['source'], entry['owner'], entry['member'])
        separator = '.' if entry['language'] == 'go' else '::'
        short = separator.join(x for x in [entry['owner'], entry['member']] if x)
        if not entry.get('reason') or not entry.get('replacement'):
            errors.append(f'{api}: reason and replacement are required')
        if entry['status'] != 'deprecated':
            errors.append(f'{api}: unsupported exception status; extend the check when adding removal history')
            continue
        expected.add(key)
        attr = source.get(key)
        if attr is None:
            errors.append(f'{api}: missing source deprecation')
            continue
        if entry['language'] == 'rust' and not re.search(r'note\s*=\s*"[^\"]+"', attr):
            errors.append(f'{api}: Rust note is required')
        since = re.search(r'since\s*=\s*"([^\"]+)"', attr)
        if entry['availability'] == 'unreleased':
            if entry['deprecated_since'] is not None or since:
                errors.append(f'{api}: unreleased deprecation must not invent a released since version')
        elif entry['availability'] == 'released':
            version = entry['deprecated_since']
            if not version or (entry['language'] == 'rust' and (not since or since[1] != version)):
                errors.append(f'{api}: released since metadata differs from source')
        else:
            errors.append(f'{api}: invalid availability')
        replacement = entry['replacement'].split('::')[-1]
        replacement_owner = entry['replacement'].split('::')[-2]
        owner = re.escape(replacement_owner)
        text = (root / entry.get('replacement_source', entry['source'])).read_text()
        impl = re.search(r"impl(?:<[^>]*>)?\s+" + owner + r"(?:<[^>]*>)?\s*\{(.*?)^\}", text, re.S | re.M)
        if entry['language'] == 'rust' and (not impl or not re.search(r'pub fn\s+' + re.escape(replacement) + r'\s*\(', impl[1])):
            errors.append(f'{api}: replacement constructor not found')
        if entry['language'] == 'go' and entry.get('replacement_kind') != 'field' and not re.search(r'func\s+\(\w+\s+\*?' + owner + r'\)\s+' + re.escape(replacement) + r'\s*\(', text):
            errors.append(f'{api}: replacement method not found')
        if entry['language'] == 'go' and entry.get('replacement_kind') == 'field':
            declaration = re.search(r'type\s+' + owner + r'\s+struct\s*\{(.*?)^\}', text, re.S | re.M)
            if not declaration or not re.search(r'\b' + re.escape(replacement) + r'\b', declaration[1]):
                errors.append(f'{api}: replacement field not found')
        for lang, doc in docs.items():
            rows = [line for line in doc.splitlines() if line.startswith('|') and f'`{short}`' in line]
            if len(rows) != 1 or 'Deprecated' not in rows[0]:
                errors.append(f'{api}: missing/duplicate status row in {lang or "ko"} guide')
            elif entry['availability'] == 'unreleased' and ('미배포' if not lang else 'unreleased') not in rows[0]:
                errors.append(f'{api}: guide must identify unreleased status')
            elif entry['availability'] == 'released' and entry['deprecated_since'] not in rows[0]:
                errors.append(f'{api}: guide must show first deprecation release')
            if replacement_owner + separator + replacement not in doc:
                errors.append(f'{api}: missing replacement in {lang or "ko"} guide')
    for key in source.keys() - expected:
        errors.append(f'unlisted source deprecation: {key}')
    return errors


def main():
    errors = inspect()
    if errors:
        raise SystemExit('\n'.join(errors))
    print('API deprecations, replacements and Korean/English lifecycle guides match.')


if __name__ == '__main__':
    main()
