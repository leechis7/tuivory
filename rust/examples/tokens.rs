use tuivory::{ColorProfile, Theme, TokenDocument};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let (theme, profile) = match args.as_slice() {
        [] => (Theme::Dark, ColorProfile::Indexed256),
        [theme, profile] => (theme.parse()?, profile.parse()?),
        _ => return Err("usage: tokens [dark|light|blackwhite 8|16|256|truecolor]".into()),
    };
    let document = TokenDocument::candidate()?;
    println!(
        "{}",
        serde_json::to_string(&document.tokens(theme, profile)?)?
    );
    Ok(())
}
