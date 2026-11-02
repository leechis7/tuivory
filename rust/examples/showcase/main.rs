// Each standalone example owns a snapshot module; reuse those entrypoints here.
#![allow(clippy::duplicate_mod)]
#[allow(dead_code)]
#[path = "../catalog/main.rs"]
mod catalog;
#[allow(dead_code)]
#[path = "../controls/main.rs"]
mod controls;
#[allow(dead_code)]
#[path = "../focus/main.rs"]
mod focus;
#[allow(dead_code)]
#[path = "../menu/main.rs"]
mod menu;
#[allow(dead_code)]
#[path = "../playground/main.rs"]
mod playground;
#[allow(dead_code)]
#[path = "../syntax/main.rs"]
mod syntax;
#[allow(dead_code)]
#[path = "../tree/main.rs"]
mod tree;
#[allow(dead_code)]
#[path = "../workspace/main.rs"]
mod workspace;

use std::error::Error;
const DEMOS: &str = "playground, tree, workspace, focus, catalog, menu, controls, syntax";
fn run() -> Result<(), Box<dyn Error>> {
    let input: Vec<String> = std::env::args().skip(1).collect();
    let mut demo = "playground".to_string();
    let mut selected = false;
    let mut forwarded = Vec::new();
    let mut list = false;
    let mut help = false;
    let en = input.iter().any(|arg| arg == "--lang=en")
        || input.windows(2).any(|pair| pair == ["--lang", "en"]);
    let mut args = input.into_iter();
    while let Some(arg) = args.next() {
        if arg == "--demo" || arg.starts_with("--demo=") {
            if selected {
                return Err("--demo must occur once".into());
            }
            demo = if arg == "--demo" {
                args.next().ok_or("--demo requires an example")?
            } else {
                arg.trim_start_matches("--demo=").to_string()
            };
            selected = true;
        } else if arg == "--list" {
            list = true;
        } else {
            help |= arg == "--help" || arg == "-h";
            // Go's flag parser accepts both --name=value and --name value.
            // Boolean switches retain their =value spelling for example parsers.
            if let Some((name, value)) = arg.split_once('=') {
                if matches!(
                    name,
                    "--lang"
                        | "--theme"
                        | "--colors"
                        | "--layout"
                        | "--focus-order"
                        | "--quit-key"
                        | "--mode"
                        | "--grid-preset"
                        | "--density"
                        | "--shadow"
                        | "--menu-id"
                        | "--snapshot"
                ) {
                    forwarded.extend([name.to_owned(), value.to_owned()]);
                } else {
                    forwarded.push(arg);
                }
            } else {
                forwarded.push(arg);
            }
        }
    }
    if list || help && !selected {
        if en {
            println!(
                "Tuivory examples — one executable\n--demo NAME [example options]   --list\nDefault: playground\nExamples: {DEMOS}"
            );
        } else {
            println!(
                "Tuivory 예제 — 단일 실행파일\n--demo 이름 [예제 옵션]   --list\n기본: playground\n예제: {DEMOS}"
            );
        }
        println!(
            "--demo tree --lang ko\n--demo syntax --lang en\n--demo catalog --mode grid\n--demo NAME --help"
        );
        return Ok(());
    }
    if help {
        if !DEMOS.split(", ").any(|name| name == demo) {
            return Err(format!("unknown demo {demo:?}; choose {DEMOS}").into());
        }
        let profiles = if demo == "playground" {
            "auto|8|16|256|truecolor"
        } else {
            "8|16|256|truecolor"
        };
        println!(
            "Tuivory --demo {demo}\n--lang ko|en --theme dark|light|blackwhite --colors {profiles}"
        );
        if demo == "playground" {
            println!("--mouse=false --snapshot FILE.svg --popup");
        } else {
            println!("--ascii --snapshot FILE.svg");
        }
        match demo.as_str() {
            "workspace" => println!(
                "--layout columns|rows --focus-order tabs,tree,content --quit-key ctrl-q|ctrl-x --drag"
            ),
            "catalog" => println!(
                "--mode forms|collections|grid|feedback|layout --grid-preset simple|data --grid-sample --density auto|compact|comfortable"
            ),
            "menu" => println!(
                "--shadow off|auto|solid (dim: whole-cell compatibility) --open --menu-id ID"
            ),
            "controls" => println!("--open"),
            _ => (),
        }
        return Ok(());
    }
    match demo.as_str() {
        "playground" => playground::run(forwarded),
        "tree" => tree::run(forwarded),
        "workspace" => workspace::run(forwarded),
        "focus" => focus::run(forwarded),
        "catalog" => catalog::run(forwarded),
        "menu" => menu::run(forwarded),
        "controls" => controls::run(forwarded),
        "syntax" => syntax::run(forwarded),
        _ => Err(format!("unknown demo {demo:?}; choose {DEMOS}").into()),
    }
}
fn main() {
    if let Err(error) = run() {
        eprintln!("TUIVORY: {error}");
        std::process::exit(1);
    }
}
