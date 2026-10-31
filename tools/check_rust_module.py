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
from build_rust import linker_environment
from check_static_elf import inspect

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ratatui', action='store_true', help='also verify the optional Ratatui adapter externally')
    parser.add_argument('--terminal-output', type=Path, help='export SDK-only terminal lifecycle test host')
    parser.add_argument('--static-output', type=Path, help='also export a static x86_64 external host')
    args = parser.parse_args()
    if args.terminal_output:
        args.ratatui = True
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
                    (', features = ["terminal"]' if args.terminal_output else ', features = ["ratatui"]' if args.ratatui else '') + ' }\n')
        (consumer / 'Cargo.toml').write_text(manifest)
        source = '''#![deny(deprecated)]
use tuivory::{Color, ColorProfile, Theme, TokenDocument};
fn main() {
    let password=tuivory::controls::Control::input("pw","Password","private",true).unwrap();
    assert_eq!(password.model.value("pw"),Some("private"));
    assert_ne!(password.model.fields()[0].value,"private");
    let mut editor=tuivory::text::TextDocument::editor("literal [error] and 한글");
    editor.buffer.handle("select_all","");
    assert_eq!(editor.handle("copy","").text,"literal [error] and 한글");
    editor.set_markup("[info]safe[/]").unwrap();
    let items=vec![tuivory::containers::LayoutItem{id:"editor".into(),..Default::default()}];
    let rects=tuivory::containers::compute_container(tuivory::layout::CellRect{x:0,y:0,width:20,height:4},&items,&tuivory::containers::ContainerOptions{kind:"row".into(),..Default::default()}).unwrap();
    assert_eq!(rects[0].rect.width,20);
    let control_state = tuivory::interaction::ControlState { read_only:true, invalid:true, edited:true, ..Default::default() };
    assert!(!control_state.visual().editable); assert_eq!(control_state.visual().role,"error"); assert_eq!(control_state.visual().markers,"!*=");
    let target = |id:&str| tuivory::interaction::FocusTarget { id:id.into(), ..Default::default() };
    let mut focus = tuivory::interaction::FocusStack::new("root",vec![target("open")]).unwrap();
    focus.open("dialog",vec![target("close")],"",true).unwrap();
    assert!(focus.route("root").blocked); assert_eq!(focus.request_close().unwrap().id,"dialog");
    focus.close("dialog").unwrap(); assert_eq!(focus.focused(),"open");
    let mut form=tuivory::forms::Form::new(vec![tuivory::forms::FormField{id:"name".into(),kind:"text".into(),required:true,..Default::default()}]).unwrap();
    assert_eq!(form.handle("submit","").kind,"invalid");form.handle("insert","External");assert_eq!(form.handle("submit","").kind,"submit");
    let mut picker=tuivory::collections::SearchPicker::new(vec![tuivory::collections::ListItem{id:"rust".into(),label:"Rust".into(),..Default::default()}]).unwrap();picker.handle("open","",4);picker.handle("insert","Rust",4);assert_eq!(picker.handle("activate","",4).id,"rust");
    let rows=tuivory::grid::MemoryRows::new(vec![tuivory::grid::GridRecord{id:"row".into(),cells:[("name".into(),"External".into())].into(),..Default::default()}]).unwrap();let mut grid=tuivory::grid::Grid::new(vec![tuivory::grid::GridColumn{id:"name".into(),width:12,editable:true,..Default::default()}],Box::new(rows)).unwrap();assert_eq!(grid.handle("copy",4).text,"External");assert_eq!(grid.handle("activate",4).kind,"edit");
    grid.set_options(tuivory::grid::grid_preset("data").unwrap()).unwrap();
    grid.set_cell_info(|_,_|tuivory::grid::GridCellInfo{display:"formatted".into(),has_display:true,metadata:"TEXT".into(),..Default::default()});
    assert!(grid.select_range(tuivory::grid::GridRange{anchor_row:"row".into(),end_row:"row".into(),anchor_column:"name".into(),end_column:"name".into()}));assert_eq!(grid.handle("copy_range",4).text,"External");
    grid.request_filter("old");let old=grid.revision();grid.request_filter("new");assert!(!grid.apply_source(old,Box::new(tuivory::grid::MemoryRows::new(vec![]).unwrap())));
    let mut menu=tuivory::menu::Menu::new(vec![tuivory::menu::MenuItem{id:"root".into(),label:"Root".into(),..Default::default()},tuivory::menu::MenuItem{id:"copy".into(),parent:"root".into(),label:"Copy".into(),mnemonic:"c".into(),..Default::default()}]).unwrap();menu.open("root","editor");let event=menu.handle("mnemonic","c",4).unwrap();assert_eq!(event.kind,"activate");assert_eq!(event.return_id,"editor");menu.open("root","editor");
    let mut notices=tuivory::feedback::NoticeQueue::new(2).unwrap();notices.push(tuivory::feedback::Notice{id:"err".into(),severity:"error".into(),expires_at:1,..Default::default()}).unwrap();assert_eq!(notices.visible(100).len(),1);let progress=tuivory::feedback::Progress{id:"load".into(),status:"loading".into(),cancellable:true,..Default::default()};assert_eq!(progress.request_cancel().kind,"cancel");
    let spacing=tuivory::layout::SpacingTokens::for_width(tuivory::layout::Density::Auto,40);assert_eq!(spacing.padding,0);let layout=tuivory::layout::stack_layout(&[tuivory::layout::StackItem{id:"main".into(),min:10,preferred:20,weight:1}],30,1).unwrap();assert_eq!(layout.slots[0].size,30);assert_eq!(tuivory::layout::Chip{id:"filter".into(),removable:true,..Default::default()}.request_remove().kind,"remove");
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
            source = source.replace('    let doc =', '''    let light=tuivory::ui::components::Styles::new(Theme::Light,ColorProfile::Ansi16).unwrap();
    let bound=light.text_on_surface("success","surface").unwrap();
    assert_eq!(bound.fg,light.role("surface").unwrap().fg);assert_eq!(bound.bg,light.role("surface").unwrap().bg);
    let styles = tuivory::ui::components::Styles::new(Theme::Dark, ColorProfile::Ansi8).unwrap();
    assert!(styles.control(control_state,true).unwrap().add_modifier.contains(tuivory::ui::style::Modifier::UNDERLINED));
    let mut terminal = tuivory::ui::Terminal::new(tuivory::ui::backend::TestBackend::new(24, 4)).unwrap();
    terminal.draw(|f| f.render_widget(tuivory::ui::components::SurfaceWidget::new(tuivory::ui::components::TextWidget{model:&mut editor,styles:&styles,focused:true},&styles),f.area())).unwrap();
    terminal.draw(|f| f.render_widget(tuivory::ui::components::ControlWidget{model:&password,styles:&styles,focused:true},f.area())).unwrap();
    terminal.draw(|f| f.render_widget(tuivory::ui::components::ContainerWidget{items:&items,options:&tuivory::containers::ContainerOptions{kind:"row".into(),..Default::default()},styles:&styles,scroll_x:0,scroll_y:0,render_child:|id:&str,area,buf:&mut tuivory::ui::buffer::Buffer|{
        assert_eq!(id,"editor");tuivory::ui::widgets::Widget::render(tuivory::ui::widgets::Paragraph::new("external"),area,buf);
    }},f.area())).unwrap();
    terminal.draw(|f| f.render_widget(styles.block("External", true).unwrap(), f.area())).unwrap();
    assert_eq!(terminal.backend().buffer()[(0, 0)].symbol(), "╔");
    let tree = tuivory::tree::Tree::new(vec![tuivory::tree::TreeNode { id: "root".into(), name: "External".into(), ..Default::default() }]).unwrap();
    let mut state = tuivory::tree::TreeState::default();
    terminal.draw(|f| f.render_stateful_widget(tuivory::ui::components::TreeWidget::new(&tree, &styles).unwrap(), f.area(), &mut state)).unwrap();
    assert_eq!(terminal.backend().buffer()[(0, 0)].symbol(), ">");
    terminal.draw(|f| f.render_stateful_widget(tuivory::ui::components::TabsWidget::new(&tabs, &styles).unwrap(),f.area(),&mut tab_state)).unwrap();
    terminal.draw(|f| f.render_widget(tuivory::ui::components::GridWidget{model:&grid,styles:&styles,focused:true},f.area())).unwrap();
    assert_eq!(terminal.backend().buffer()[(grid.geometry(24,4).gutter as u16-1,0)].symbol(),"│");
    let mut menu_terminal=tuivory::ui::Terminal::new(tuivory::ui::backend::TestBackend::new(40,10)).unwrap();
    menu_terminal.draw(|f|f.render_widget(tuivory::ui::components::MenuPopupWidget::new(&mut menu,&styles,"Menu").ascii(true).padding(1),f.area())).unwrap();assert_eq!(menu_terminal.backend().buffer()[(0,0)].symbol(),"+");assert_eq!(menu_terminal.backend().buffer()[(2,2)].symbol(),">");
    menu_terminal.draw(|f|f.render_widget(tuivory::ui::components::MenuWidget::new(&mut menu,&styles).ascii(true),f.area())).unwrap();assert_eq!(menu_terminal.backend().buffer()[(0,0)].symbol(),">");
    menu_terminal.draw(|f|f.render_widget(tuivory::ui::components::MenuBarWidget::new(&mut menu,&styles),f.area())).unwrap();assert_eq!(menu_terminal.backend().buffer()[(2,0)].symbol(),"R");
    assert_eq!(menu.return_id(),"editor");
    let runs = tuivory::components::status_line(&[tuivory::components::StatusItem { id: "e".into(), text: "Failure".into(),role: "error".into(),priority:10 }],24).runs;
    terminal.draw(|f| f.render_widget(tuivory::ui::components::LineWidget::new(runs.clone(),&styles).unwrap(),f.area())).unwrap();
    terminal.draw(|f| f.render_widget(styles.panel("External",true,1,true).unwrap(),f.area())).unwrap();
    assert_eq!(terminal.backend().buffer()[(0, 0)].symbol(), "+");
    let doc =''')
        if args.terminal_output:
            source=source.replace('fn main() {', '''fn main() {
    if let Ok(mode)=std::env::var("TUIVORY_SESSION_TEST") {
        use tuivory::ui::Session;
        if mode=="foreign-raw" {
            use tuivory::ui::terminal::terminal::{enable_raw_mode,disable_raw_mode,is_raw_mode_enabled};
            enable_raw_mode().unwrap();
            assert_eq!(Session::enter(Default::default()).err().unwrap().kind(),std::io::ErrorKind::AlreadyExists);
            assert!(is_raw_mode_enabled().unwrap());
            disable_raw_mode().unwrap();println!("FOREIGN_RAW_OK");return;
        }
        if mode=="no-tty" {
            for _ in 0..2 { assert_ne!(Session::enter(Default::default()).err().unwrap().kind(),std::io::ErrorKind::AlreadyExists); }
            println!("NO_TTY_OK");return;
        }
        let guard=Session::enter(Default::default()).unwrap();
        assert_eq!(Session::enter(Default::default()).err().unwrap().kind(),std::io::ErrorKind::AlreadyExists);
        if mode=="panic" {panic!("expected session unwind test");}
        guard.finish().unwrap();
        let guard=Session::enter(Default::default()).unwrap();drop(guard);
        println!("SESSION_OK");return;
    }
''',1)
        (consumer / 'src/main.rs').write_text(source)
        shutil.copyfile(module / 'Cargo.lock', consumer / 'Cargo.lock')
        subprocess.run(['cargo', 'run', '--manifest-path', str(consumer / 'Cargo.toml'), '--offline'],
                       env=env, check=True)
        if args.terminal_output:
            args.terminal_output.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(base/'target/debug/tuivory-external-check',args.terminal_output)
        if args.ratatui:
            legacy = r'''#![deny(deprecated)]
use tuivory::{menu::{Menu,MenuItem},ui::components::{Styles,MenuWidget,MenuBarWidget,MenuPopupWidget},Theme,ColorProfile};
fn main() {
    let styles=Styles::new(Theme::Dark,ColorProfile::Ansi8).unwrap();
    let mut menu=Menu::new(vec![MenuItem{id:"a".into(),label:"A".into(),..Default::default()}]).unwrap();
    let _=MenuWidget{model:&mut menu,styles:&styles,ascii:false,focused:false};
    let _=MenuBarWidget{model:&mut menu,styles:&styles,focused:false};
    let _=MenuPopupWidget{model:&mut menu,styles:&styles,title:"Menu",ascii:false,focused:false,padding:1};
    let rows=tuivory::grid::MemoryRows::new(vec![]).unwrap();
    let mut grid=tuivory::grid::Grid::new(vec![],Box::new(rows)).unwrap();
    let _=grid.click("","",0,40,8);
}
'''
            main_file = consumer / 'src/main.rs'
            try:
                main_file.write_text(legacy)
                check = subprocess.run(['cargo','check','--manifest-path',str(consumer/'Cargo.toml'),
                                        '--offline','--message-format=json'],env=env,text=True,capture_output=True)
                diagnostics = [json.loads(line) for line in check.stdout.splitlines() if line.startswith('{')]
                deprecated = [d['message']['message'] for d in diagnostics
                              if d.get('reason') == 'compiler-message' and
                              (d['message'].get('code') or {}).get('code') == 'deprecated']
                assert check.returncode != 0 and len(deprecated) == 4, (check.stdout,check.stderr)
                print('External compiler rejects all four legacy Rust APIs under deny(deprecated).')
            finally:
                main_file.write_text(source)
        if args.static_output:
            target = 'x86_64-unknown-linux-musl'
            static_env = dict(linker_environment(target), CARGO_TARGET_DIR=env['CARGO_TARGET_DIR'])
            subprocess.run(['cargo', 'build', '--manifest-path', str(consumer / 'Cargo.toml'),
                            '--offline', '--locked', '--release', '--target', target], env=static_env, check=True)
            binary = base / 'target' / target / 'release/tuivory-external-check'
            inspect(binary, 'x86_64')
            args.static_output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(binary, args.static_output)
    adapter = ' with Ratatui' if args.ratatui else ''
    print(f'Packaged Rust crate and external project{adapter} passed without repository design assets.')


if __name__ == '__main__':
    main()
