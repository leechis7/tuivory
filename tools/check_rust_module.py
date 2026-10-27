#!/usr/bin/env python3
"""Package Rust on its own and test it from an external path dependency."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ratatui', action='store_true', help='also verify the optional Ratatui adapter externally')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='tuivory-rust-module-') as temporary:
        base = Path(temporary)
        module = base / 'module'
        shutil.copytree(ROOT / 'rust', module, ignore=shutil.ignore_patterns('target'))
        env = dict(os.environ, CARGO_TARGET_DIR=str(base / 'target'))
        # No repository design/ directory is available to this module.
        subprocess.run(['cargo', 'package', '--manifest-path', str(module / 'Cargo.toml'),
                        '--locked'], env=env, check=True)
        package = next((base / 'target/package').glob('tuivory-*.crate'))
        with tarfile.open(package) as archive:
            archive.extractall(base / 'unpacked', filter='data')
        dependency = next((base / 'unpacked').iterdir())
        consumer = base / 'consumer'
        (consumer / 'src').mkdir(parents=True)
        # JSON quoting is valid for these TOML basic strings and escapes paths.
        manifest = ('[package]\nname = "tuivory-external-check"\nversion = "0.0.0"\n'
                    'edition = "2024"\n\n[dependencies]\n'
                    'tuivory = { path = ' + json.dumps(str(dependency)) +
                    (', features = ["ratatui"]' if args.ratatui else '') + ' }\n')
        if args.ratatui:
            manifest += 'ratatui = { version = "0.30.2", default-features = false }\n'
        (consumer / 'Cargo.toml').write_text(manifest)
        source = '''use tuivory::{Color, ColorProfile, Theme, TokenDocument};
fn main() {
    let tree = tuivory::tree::Tree::new(vec![tuivory::tree::TreeNode { id: "root".into(), name: "External".into(), branch: true, ..Default::default() }]).unwrap();
    let mut state = tuivory::tree::TreeState::default();
    assert!(matches!(tree.handle(&mut state, tuivory::tree::TreeAction::Right, 4), Some(tuivory::tree::TreeEvent::Expand(_))));
    let tabs = tuivory::components::Tabs::new(vec![tuivory::components::TabItem { id: "a".into(), title: "Overview".into(), ..Default::default() },tuivory::components::TabItem { id: "b".into(), title: "Draft".into(), edited: true, closable: true, ..Default::default() }]).unwrap();
    let mut tab_state = tuivory::components::TabState::default();
    tabs.handle(&mut tab_state,tuivory::components::TabAction::Next);
    assert_eq!(tab_state.active,"a"); assert_eq!(tab_state.focused,"b");
    let split = tuivory::components::SplitSpec { first_min: 5,second_min: 5 };
    assert_eq!(split.layout(&tuivory::components::SplitState { preferred: 8 },30).first,8);
    let path = tuivory::components::breadcrumbs(&[tuivory::components::PathItem { id: "current".into(), label: "Current".into() }],20);
    assert_eq!(path[0].id,"current");
    let doc = TokenDocument::candidate().unwrap();
    assert_eq!(doc.roles().len(), 16);
    assert_eq!(doc.palette_names().count(), 12);
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [ColorProfile::Ansi8, ColorProfile::Ansi16, ColorProfile::Indexed256, ColorProfile::Truecolor] {
            let palette = doc.palette(theme, profile).unwrap();
            assert_eq!(palette.styles().len(), 16);
            assert!(palette.style("selection").is_ok());
        }
    }
    let style = doc.palette(Theme::Dark, ColorProfile::Ansi8).unwrap().style("body").unwrap();
    assert!(matches!(style.foreground, Color::Indexed(_)));
}
'''
        if args.ratatui:
            source = source.replace('    let doc =', '''    let styles = tuivory::ratatui::Styles::new(Theme::Dark, ColorProfile::Ansi8).unwrap();
    let mut terminal = ratatui::Terminal::new(ratatui::backend::TestBackend::new(24, 4)).unwrap();
    terminal.draw(|f| f.render_widget(styles.block("External", true).unwrap(), f.area())).unwrap();
    assert_eq!(terminal.backend().buffer()[(0, 0)].symbol(), "╔");
    let tree = tuivory::tree::Tree::new(vec![tuivory::tree::TreeNode { id: "root".into(), name: "External".into(), ..Default::default() }]).unwrap();
    let mut state = tuivory::tree::TreeState::default();
    terminal.draw(|f| f.render_stateful_widget(tuivory::ratatui::TreeWidget::new(&tree, &styles).unwrap(), f.area(), &mut state)).unwrap();
    assert_eq!(terminal.backend().buffer()[(0, 0)].symbol(), ">");
    terminal.draw(|f| f.render_stateful_widget(tuivory::ratatui::TabsWidget::new(&tabs, &styles).unwrap(),f.area(),&mut tab_state)).unwrap();
    let runs = tuivory::components::status_line(&[tuivory::components::StatusItem { id: "e".into(), text: "Failure".into(),role: "error".into(),priority:10 }],24).runs;
    terminal.draw(|f| f.render_widget(tuivory::ratatui::LineWidget::new(runs.clone(),&styles).unwrap(),f.area())).unwrap();
    terminal.draw(|f| f.render_widget(styles.panel("External",true,1,true).unwrap(),f.area())).unwrap();
    assert_eq!(terminal.backend().buffer()[(0, 0)].symbol(), "+");
    let doc =''')
        (consumer / 'src/main.rs').write_text(source)
        shutil.copyfile(module / 'Cargo.lock', consumer / 'Cargo.lock')
        subprocess.run(['cargo', 'run', '--manifest-path', str(consumer / 'Cargo.toml'), '--offline'],
                       env=env, check=True)
    adapter = ' with Ratatui' if args.ratatui else ''
    print(f'Packaged Rust crate and external project{adapter} passed without repository design assets.')


if __name__ == '__main__':
    main()
