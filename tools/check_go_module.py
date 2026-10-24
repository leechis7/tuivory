#!/usr/bin/env python3
"""Verify that go/ works without the repository's shared design directory."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='tuivory-go-module-') as temporary:
        base = Path(temporary)
        module = base / 'module'
        shutil.copytree(ROOT / 'go', module, ignore=shutil.ignore_patterns('bin', '__pycache__'))
        # No shared design/ directory is copied. All required runtime assets
        # must be inside the distributable Go module.
        env = dict(os.environ, GOWORK='off')
        subprocess.run(['go', 'test', './...'], cwd=module, env=env, check=True)
        consumer = base / 'consumer'
        consumer.mkdir()
        (consumer / 'go.mod').write_text(
            'module example.com/tuivory-isolated-consumer\n\ngo 1.24.0\n\n'
            'require github.com/leechis7/tuivory/go v0.0.0\n'
            'replace github.com/leechis7/tuivory/go => {}\n'.format(module))
        # Keep dependency checksum verification using the module's checked-in
        # sums, without requiring an unnecessary network lookup for known deps.
        shutil.copyfile(module / 'go.sum', consumer / 'go.sum')
        (consumer / 'consumer_test.go').write_text('''package consumer_test
import (
    "testing"
    "github.com/leechis7/tuivory/go"
)
func TestIsolatedModule(t *testing.T) {
    theme, err := tuivory.New("dark", "256")
    if err != nil { t.Fatal(err) }
    if theme.Styles.Profile() != "256" { t.Fatal("profile missing") }
    document, err := tuivory.CandidateTokens()
    if err != nil { t.Fatal(err) }
    palette, err := document.Palette("light", "16")
    if err != nil { t.Fatal(err) }
    if _, err := tuivory.Resolve(palette); err != nil { t.Fatal(err) }
}
''')
        subprocess.run(['go', 'test', '-mod=mod', './...'], cwd=consumer, env=env, check=True)
    print('Go module and single-import consumer passed without repository design assets.')


if __name__ == '__main__':
    main()
