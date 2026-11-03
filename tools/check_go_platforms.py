#!/usr/bin/env python3
"""Compile a root-only SDK consumer across OSes; native checks use a simulation screen.

Consumer artifacts stay in .cache/, never in bin/ or release archives. This does
not cross-build the distributed examples or claim physical terminal coverage.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [('windows', 'amd64'), ('windows', 'arm64'), ('linux', 'amd64'),
           ('linux', 'arm64'), ('darwin', 'amd64'), ('darwin', 'arm64')]
SOURCE = '''package main
import ui "github.com/leechis7/tuivory/go"
var _ func() (ui.Screen,error) = ui.NewScreen
var _ func() (ui.Screen,error) = ui.NewConsoleScreen
var _ func() (ui.Tty,error) = ui.NewDevTty
func main() {
    _ = ui.NewApplication().SetRoot(ui.NewWidgetTextView().SetText("SDK"),true)
    s:=ui.NewSimulationScreen("UTF-8");if err:=s.Init();err!=nil {panic(err)};defer s.Fini()
    s.SetSize(8,2);ui.WideSafeScreen(s).Put(1,0,"한",ui.StyleDefault);s.Show()
    cells,_,_:=s.GetContents();if string(cells[1].Bytes)!="한" {panic("wide output")}
    println("SDK_ROOT_OK")
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', action='store_true', help='build/run only the current Go host, no physical terminal')
    parser.add_argument('--version', help='test an exact public SDK version without a local replace, e.g. v0.10.2')
    args = parser.parse_args()
    env = dict(os.environ, CGO_ENABLED='0', GOWORK='off')
    host = tuple(subprocess.check_output(['go', 'env', 'GOOS', 'GOARCH'], env=env, text=True).split())
    targets = [host] if args.native else TARGETS
    cache = ROOT / '.cache/validation/go-platforms'
    if args.version:
        if not args.version.startswith('v') or any(c not in 'v0123456789.-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' for c in args.version):
            parser.error('invalid public version')
        cache = cache / ('public-' + args.version)
    cache.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='consumer-', dir=cache) as tmp:
        consumer = Path(tmp)
        dependency = 'require github.com/leechis7/tuivory/go ' + (args.version or 'v0.0.0') + '\n'
        if not args.version:
            dependency += 'replace github.com/leechis7/tuivory/go => ' + json.dumps(str(ROOT / 'go')) + '\n'
        (consumer / 'go.mod').write_text('module example.com/tuivory-platform-check\n\ngo 1.24.0\n\n' + dependency, encoding="utf-8")
        (consumer / 'main.go').write_text(SOURCE, encoding="utf-8")
        (consumer / 'posix.go').write_text('//go:build linux || darwin\n\npackage main\nimport ui "github.com/leechis7/tuivory/go"\nvar _ func() (ui.Tty,error) = ui.NewStdIoTty\nvar _ func(string) (ui.Tty,error) = ui.NewDevTtyFromDev\n', encoding="utf-8")
        shutil.copy2(ROOT / 'go/go.sum', consumer / 'go.sum')
        subprocess.run(['go', 'mod', 'tidy'], cwd=consumer, env=env, check=True)
        if args.version:
            metadata = json.loads(subprocess.check_output(['go', 'list', '-m', '-json', 'github.com/leechis7/tuivory/go'], cwd=consumer, env=env, text=True))
            assert metadata['Version'] == args.version and 'Replace' not in metadata
        for goos, goarch in targets:
            target_env = dict(env, GOOS=goos, GOARCH=goarch)
            output = cache / (f'{goos}-{goarch}' + ('.exe' if goos == 'windows' else ''))
            subprocess.run(['go', 'build', '-o', str(output), '.'], cwd=consumer, env=target_env, check=True)
            if args.native:
                result = subprocess.run([str(output)], capture_output=True, text=True, check=True)
                assert 'SDK_ROOT_OK' in result.stdout + result.stderr
            if goos == 'windows':
                negative = consumer / 'unsupported_windows.go'
                negative.write_text('package main\nimport ui "github.com/leechis7/tuivory/go"\nvar _ = ui.NewStdIoTty\n', encoding="utf-8")
                try:
                    failure = subprocess.run(['go', 'build', '-o', str(output) + '.unsupported', '.'], cwd=consumer, env=target_env, capture_output=True, text=True)
                    assert failure.returncode != 0 and 'undefined: ui.NewStdIoTty' in failure.stderr, failure.stderr
                    assert 'undefined: native.' not in failure.stderr
                finally:
                    negative.unlink()
            results.append({'os': goos, 'arch': goarch, 'compile': 'passed', 'native_simulation': args.native})
            print(f'PASS {goos}/{goarch} root-only consumer' + (' and native simulation' if args.native else ' (compile only)'), flush=True)
    name = ('native-' + '-'.join(host)) if args.native else 'cross-compile'
    (cache / (name + '.json')).write_text(json.dumps({'results': results, 'dependency': args.version or 'working-source', 'physical_terminal': 'not-tested'}, indent=2) + '\n', encoding="utf-8")


if __name__ == '__main__':
    main()
