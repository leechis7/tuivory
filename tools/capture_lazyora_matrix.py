#!/usr/bin/env python3
"""Capture original LazyOra style functions without importing its application/DB."""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def function(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def program(source):
    theme = (source / 'theme.go').read_text()
    tokens = (source / 'style_tokens.go').read_text()
    widgets = (source / 'widgets.go').read_text()
    grid = (source / 'grid.go').read_text()
    syntax = (source / 'sql_colors.go').read_text()
    parts = [theme[theme.index('type themeColors struct'):theme.index('\nvar palette')]]
    for name in ['palette', 'lightPalette', 'blackWhitePalette', 'darkANSI', 'lightANSI']:
        start = theme.index('var ' + name + ' =')
        parts.append(theme[start:theme.index('\n}', start) + 2])
    parts.append(tokens[tokens.index('// Profiles describe'):tokens.index('func (s *screen) colorProfile()')])
    parts.append(tokens[tokens.index('func indexed('):tokens.index('\ntype surfaceRole')])
    parts.append(tokens[tokens.index('type surfaceRole'):tokens.index('func (s *screen) setSurface')])
    parts.append(widgets[widgets.index('type textRole'):widgets.index('// Constructors')])
    for method in ['fieldStyle', 'focusStyle', 'buttonFocusStyle', 'buttonStyle', 'editorStyle', 'borderColor', 'colors']:
        parts.append(function(theme, 'func (s *screen) ' + method + '('))
    parts.append(function(tokens, 'func (s *screen) disabledStyle('))
    parts.append(function((source / 'grid_inline.go').read_text(), 'func (s *screen) editedCellStyle('))
    parts.append(grid[grid.index('type gridColors struct'):grid.index('func (s *screen) gridHeaderStyle')])
    parts.append(grid[grid.index('var lightGridPalette'):])
    for method in ['gridHeaderStyle', 'gridActiveStyle', 'gridBaseStyle']:
        parts.append(function(grid, 'func (s *screen) ' + method + '('))
    parts.append(syntax[syntax.index('type sqlColorKind'):syntax.index('type sqlColorSpan')])
    parts.append(syntax[syntax.index('var sqlRichColors'):syntax.index('func (s *screen) colorEditor')])
    parts.append(function(syntax, 'func (s *screen) profileSQLStyle('))
    parts.append(function((source / 'choice.go').read_text(), 'func (s *screen) styleChoice('))
    parts.append('''
type choiceField struct { *tview.DropDown; background, foreground tcell.Color }
type cell struct { Null bool }
type screen struct { prefs struct { Theme string }; profile colorProfile; table *tview.Table; resultValues [][]cell }
func (s *screen) colorProfile() colorProfile { return s.profile }
func (s *screen) monochrome() bool { return s.prefs.Theme == "blackwhite" }
func (s *screen) ansiColors() bool { return s.profile==profileANSI8 || s.profile==profileANSI16 }
func snapshot(st tcell.Style) [3]uint64 { fg,bg,a:=st.Decompose(); return [3]uint64{uint64(fg),uint64(bg),uint64(a)} }
func main() {
 result:=map[string]map[string][3]uint64{}
 for _,theme:=range []string{"dark","light","blackwhite"} {
 for name,profile:=range map[string]colorProfile{"8":profileANSI8,"16":profileANSI16,"256":profile256,"truecolor":profileRGB} {
 s:= &screen{profile:profile,table:tview.NewTable(),resultValues:[][]cell{{{}},{{}}}};s.prefs.Theme=theme
 m:=map[string][3]uint64{}; put:=func(name string,st tcell.Style){m[name]=snapshot(st)}
 put("field",s.fieldStyle());put("selection",s.focusStyle());put("button",s.buttonStyle());put("button.focus",s.buttonFocusStyle());put("disabled",s.disabledStyle());put("edited",s.editedCellStyle());put("editor",s.editorStyle())
 for surface:=surfaceCanvas;surface<=surfaceEditor;surface++ {
 for role:=textBody;role<=textWarning;role++ {
 fg:=s.textColor(role);if surface==surfaceField{fg=s.colors().fieldText}
 put(fmt.Sprintf("text/%d/%d",surface,role),tcell.StyleDefault.Foreground(fg).Background(s.surfaceColor(surface)))
 }
 for _,focused:=range []bool{false,true} {
 bg:=s.surfaceColor(surface);put(fmt.Sprintf("border/%d/%t",surface,focused),tcell.StyleDefault.Foreground(s.borderColor(focused,bg)).Background(bg))
 }}
 for _,active:=range []bool{false,true} {put(fmt.Sprintf("header/%t",active),s.gridHeaderStyle(active))}
 for _,focused:=range []bool{false,true} {
 for _,edited:=range []bool{false,true} {
 st:=s.gridActiveStyle(focused);if edited {st=s.editedCellStyle().Underline(focused)}
 put(fmt.Sprintf("active/%t/%t",focused,edited),st)
 }}
 for row:=1;row<=2;row++ {for _,current:=range []bool{false,true} {for _,null:=range []bool{false,true} {for _,edited:=range []bool{false,true} {for _,inRange:=range []bool{false,true} {
 selected:=3;if current{selected=row};s.table.Select(selected,0);s.resultValues[row-1][0].Null=null
 st:=s.gridBaseStyle(row,0);if edited{st=s.editedCellStyle()};if inRange{st=s.fieldStyle().Underline(true)}
 put(fmt.Sprintf("cell/%d/%t/%t/%t/%t",row,current,null,edited,inRange),st)
 }}}}}
 for surface:=surfaceCanvas;surface<=surfaceEditor;surface++ {for kind:=sqlKeyword;kind<=sqlBind;kind++ {
 base:=tcell.StyleDefault.Foreground(s.surfaceText(surface)).Background(s.surfaceColor(surface))
 put(fmt.Sprintf("syntax/%d/%d",surface,kind),s.profileSQLStyle(kind,base))
 }}
 choice:=&choiceField{DropDown:tview.NewDropDown()};s.styleChoice(choice)
 put("dropdown",tcell.StyleDefault.Foreground(choice.foreground).Background(choice.background))
 g:=s.gridColors();v:=reflect.ValueOf(g)
 for i:=0;i<v.NumField();i++ {m["gridcolor/"+v.Type().Field(i).Name]=[3]uint64{v.Field(i).Uint(),0,0}}

 put("tab/false",s.buttonStyle());put("tab/true",s.buttonFocusStyle())
 put("footer",tcell.StyleDefault.Foreground(s.colors().text).Background(s.colors().footer))
 put("comparison/true",s.fieldStyle().Underline(true))
 comparison:=s.focusStyle().Underline(true);if s.monochrome(){comparison=tcell.StyleDefault.Foreground(tcell.ColorBlack).Background(tcell.ColorSilver)};put("comparison/false",comparison)
 put("splitter",tcell.StyleDefault.Foreground(s.colors().button).Background(s.colors().background))
 divider:=s.gridColors().divider;if s.ansiColors()&&!s.monochrome(){divider=tcell.ColorTeal};m["divider"]=[3]uint64{uint64(divider),0,0}
 gutter:=tcell.StyleDefault.Foreground(s.gridColors().muted).Background(s.gridColors().background)
 if s.ansiColors()&&!s.monochrome(){gutter=tcell.StyleDefault.Foreground(tcell.ColorSilver).Background(tcell.ColorBlack);if theme=="light"{gutter=gutter.Foreground(s.colors().muted).Background(s.colors().background)}};put("gutter",gutter)
 bar:=tcell.StyleDefault.Foreground(s.colors().muted).Background(s.colors().surface)
 if s.ansiColors()&&!s.monochrome(){bar=s.focusStyle();if theme=="light"{bar=bar.Foreground(tcell.ColorBlack).Background(tcell.ColorSilver)}};put("gridstatus",bar)
 put("popupcard",tcell.StyleDefault.Foreground(s.colors().text).Background(s.colors().surface));put("popupshadow",tcell.StyleDefault.Background(tcell.ColorBlack))
 for _,limited:=range []bool{false,true}{backdrop:=tcell.StyleDefault.Bold(true).Foreground(s.colors().muted).Background(s.colors().background).Dim(true);if limited{backdrop=backdrop.Foreground(tcell.ColorSilver).Background(tcell.ColorBlack)};put(fmt.Sprintf("popupbackdrop/%t",limited),backdrop)}
 result[theme+"-"+name]=m
 }}
 enc:=json.NewEncoder(os.Stdout);enc.SetIndent("","  ");if err:=enc.Encode(result);err!=nil{panic(err)}
}
''')
    return 'package main\nimport("encoding/json";"fmt";"os";"reflect";"github.com/gdamore/tcell/v2";"github.com/rivo/tview")\n' + '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='LazyOra checkout at the documented source commit')
    args = parser.parse_args()
    source_root = args.source.resolve()
    files = ['theme.go', 'style_tokens.go', 'widgets.go', 'grid.go', 'grid_inline.go', 'sql_colors.go', 'choice.go']
    paths = ['internal/ui/' + name for name in files]
    subprocess.run(['git', '-C', str(source_root), 'diff', '--exit-code', 'HEAD', '--'] + paths, check=True, capture_output=True)
    commit = subprocess.run(['git', '-C', str(source_root), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory(prefix='tuivory-matrix-') as tmp:
        main_file = Path(tmp) / 'main.go'
        main_file.write_text(program(source_root / 'internal/ui'))
        result = subprocess.run(['go', 'run', str(main_file)], cwd=ROOT / 'go', env=os.environ, check=True, capture_output=True)
    target = ROOT / 'go/internal/style/testdata/lazyora-matrix.json'
    target.write_bytes(result.stdout)
    manifest = {
        'repository': 'https://github.com/leechis7/lazyora', 'commit': commit,
        'files': {name: hashlib.sha256((source_root / name).read_bytes()).hexdigest() for name in paths},
    }
    (target.parent / 'lazyora-source.json').write_text(json.dumps(manifest, indent=2) + '\n')
    matrix = json.loads(result.stdout)
    print('Captured {} original styles across {} profiles.'.format(sum(map(len, matrix.values())), len(matrix)))


if __name__ == '__main__':
    main()
