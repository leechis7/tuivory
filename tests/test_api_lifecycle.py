import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_api_lifecycle import inspect


class LifecycleFailures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        data = json.loads((ROOT / 'design/api-lifecycle.json').read_text())
        paths = {'design/api-lifecycle.json', 'docs/api-lifecycle.md', 'docs/api-lifecycle.en.md'}
        for entry in data['entries']:
            paths.add(entry['source'])
            paths.add(entry.get('replacement_source', entry['source']))
        for name in paths:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)

    def test_unlisted_source_annotation_fails(self):
        path = self.root / 'rust/src/new.rs'
        path.write_text('pub struct Extra {\n#[deprecated(note="Use a replacement")]\npub obsolete: bool,\n}\n')
        self.assertTrue(any('unlisted source' in e for e in inspect(self.root)))

    def test_missing_english_status_row_fails(self):
        path = self.root / 'docs/api-lifecycle.en.md'
        path.write_text('\n'.join(line for line in path.read_text().splitlines() if not line.startswith('| Rust `MenuWidget::focused`')))
        self.assertTrue(any('missing/duplicate status' in e for e in inspect(self.root)))

    def test_unreleased_since_version_fails(self):
        path = self.root / 'design/api-lifecycle.json'
        data = json.loads(path.read_text())
        data['entries'][0]['availability'] = 'unreleased'
        data['entries'][0]['deprecated_since'] = '0.4.0'
        path.write_text(json.dumps(data))
        self.assertTrue(any('must not invent' in e for e in inspect(self.root)))

    def test_deleted_source_marker_fails(self):
        path = self.root / 'go/internal/style/styles.go'
        path.write_text(path.read_text().replace('// Deprecated: Use TextStyle(Field, Body), which has the same colors and attributes.',''))
        self.assertTrue(any('missing source deprecation' in e for e in inspect(self.root)))

    def test_missing_constructor_fails(self):
        path = self.root / 'rust/src/ratatui/menu.rs'
        path.write_text(path.read_text().replace('pub fn new(', 'pub fn create(', 1))
        self.assertTrue(any('replacement constructor not found' in e for e in inspect(self.root)))

    def test_missing_live_selection_field_fails(self):
        path = self.root / 'go/internal/style/theme.go'
        path.write_text(path.read_text().replace('SelectionFG', 'RenamedSelectionForeground'))
        self.assertTrue(any('replacement field not found' in e for e in inspect(self.root)))
