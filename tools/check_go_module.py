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
    "github.com/gdamore/tcell/v2"
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
    colors, _ := tuivory.Resolve(palette)
    tree, err := tuivory.NewTree([]tuivory.TreeNode{{ID:"root",Name:"External"},{ID:"child",Parent:"root",Name:"Child"}})
    if err != nil { t.Fatal(err) }
    state := &tuivory.TreeState{}
    if tree.Handle(state,tuivory.TreeRight,4).Kind != "expand" { t.Fatal("tree expansion failed") }
    view, err := tuivory.NewTreeView(tree,state,colors)
    if err != nil { t.Fatal(err) }
    screen := tcell.NewSimulationScreen("UTF-8")
    if err := screen.Init(); err != nil { t.Fatal(err) }
    defer screen.Fini()
    screen.SetSize(30,6)
    view.SetRect(0,0,30,6)
    view.Draw(screen)
    marker,_,_,_ := screen.GetContent(1,1)
    if marker != '>' { t.Fatal("external tree did not render") }
    tabs, err := tuivory.NewTabs([]tuivory.TabItem{{ID:"a",Title:"Overview"},{ID:"b",Title:"Draft",Edited:true,Closable:true}})
    if err != nil { t.Fatal(err) }
    tabState := &tuivory.TabState{}
    tabs.Handle(tabState,tuivory.TabNext)
    if tabState.Active != "a" || tabState.Focused != "b" { t.Fatal("tab focus activated content") }
    tabView, err := tuivory.NewTabView(tabs,tabState,colors)
    if err != nil { t.Fatal(err) }
    tabView.SetRect(0,0,30,1)
    tabView.Draw(screen)
    panel, err := tuivory.NewPanelView(view,colors)
    if err != nil { t.Fatal(err) }
    panel.SetRect(0,0,30,6)
    panel.Draw(screen)
    if layout := (tuivory.SplitSpec{FirstMin:5,SecondMin:5}).Layout(&tuivory.SplitState{Preferred:8},30); layout.First!=8 { t.Fatal(layout) }
    crumbs, err := tuivory.NewBreadcrumbView([]tuivory.PathItem{{ID:"root",Label:"Workspace"},{ID:"current",Label:"Current"}},colors)
    if err != nil { t.Fatal(err) }
    crumbs.SetRect(0,0,20,1); crumbs.Draw(screen)
    status, err := tuivory.NewStatusView([]tuivory.StatusItem{{ID:"e",Text:"Failure",Role:"error",Priority:10}},colors)
    if err != nil { t.Fatal(err) }
    status.SetRect(0,0,20,1); status.Draw(screen)
}
''')
        subprocess.run(['go', 'test', '-mod=mod', './...'], cwd=consumer, env=env, check=True)
    print('Go module and single-import consumer passed without repository design assets.')


if __name__ == '__main__':
    main()
