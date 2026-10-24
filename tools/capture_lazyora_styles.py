#!/usr/bin/env python3
import os, subprocess, tempfile
from pathlib import Path
import argparse
parser = argparse.ArgumentParser(description='Capture pure palette/token output from a local LazyOra checkout; no DB imports.')
parser.add_argument('source', type=Path, help='LazyOra checkout directory')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
src = args.source.resolve() / 'internal/ui'
theme=(src/'theme.go').read_text(); tokens=(src/'style_tokens.go').read_text()
parts=[theme[theme.index('type themeColors struct'):theme.index('\nvar palette')]]
for name in ['palette','lightPalette','blackWhitePalette','darkANSI','lightANSI']:
    start=theme.index('var '+name+' ='); parts.append(theme[start:theme.index('\n}', start)+2])
start=tokens.index('// Profiles describe'); end=tokens.index('func (s *screen) colorProfile()', start)
parts.append(tokens[start:end])
start=tokens.index('func indexed('); end=tokens.index('\ntype surfaceRole',start)
parts.append(tokens[start:end])
parts.append('''type screen struct { prefs struct { Theme string }; profile colorProfile }
func(s *screen) colorProfile() colorProfile { return s.profile }
func(s *screen) monochrome() bool { return s.prefs.Theme == "blackwhite" }
func main() {
 result := map[string]map[string]tcell.Color{}
 for _, theme := range []string{"dark","light","blackwhite"} {
 for profile, p := range map[string]colorProfile{"8":profileANSI8,"16":profileANSI16,"256":profile256,"truecolor":profileRGB} {
 s:= &screen{profile:p}; s.prefs.Theme=theme
 value:=s.tokens(); fields:=map[string]tcell.Color{}
 v:=reflect.ValueOf(value.themeColors)
 for i:=0;i<v.NumField();i++ { fields[v.Type().Field(i).Name]=tcell.Color(v.Field(i).Uint()) }
 v=reflect.ValueOf(value)
 for i:=1;i<v.NumField();i++ { fields[v.Type().Field(i).Name]=tcell.Color(v.Field(i).Uint()) }
 result[theme+"-"+profile]=fields
 }}
 encoder:=json.NewEncoder(os.Stdout); encoder.SetIndent("","  "); if err:=encoder.Encode(result);err!=nil {panic(err)}
}''')
with tempfile.TemporaryDirectory(prefix='tuivory-source-') as tmp:
 p=Path(tmp)/'main.go'
 p.write_text('package main\nimport("encoding/json";"os";"reflect";"github.com/gdamore/tcell/v2")\n'+'\n'.join(parts))
 r=subprocess.run(['go','run',str(p)],check=True,capture_output=True,env=os.environ, cwd=root / 'go')
 target=root / 'go/internal/style/testdata/lazyora-styles.json'; target.parent.mkdir(exist_ok=True); target.write_bytes(r.stdout)
