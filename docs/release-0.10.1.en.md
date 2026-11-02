# Tuivory 0.10.1 release

[한국어 (default)](release-0.10.1.md) · **English**

Go/Rust auto/solid popup shadows now use **one cell right and half a row down**. Keep borders and the off default; frameless and right-only comparison designs are not applied. Dark shades use actual-backdrop contrast with RGB 40% brightness, while light shades use 80%. Black backgrounds and low-color terminals use documented fallbacks.

```sh
go get github.com/leechis7/tuivory/go@v0.10.1
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.1", features = ["ratatui"] }
```

The public API names remain unchanged. Enabled default allocation becomes one cell narrower; use returned Card/Bounds for layout and hit testing. Half rows still reserve one terminal row. Half blocks replace backdrop text; ASCII uses dots. Dim remains whole-cell compatibility outside the example cycle. [API and migration details](popup-shadows.en.md).

Go 1.24+, Rust core 1.85+, UI/examples 1.88+. Rust is Git-distributed, not published to crates.io. Linux ARM64/x86_64 archives each contain one static executable per language, built on native hosts without cross compilation. [Examples](examples.en.md) · [Static builds](static-build.en.md).

```sh
./bin/go/tuivory-linux-arm64 --demo menu --shadow auto --lang en
./bin/rust/tuivory-linux-arm64 --demo menu --shadow auto --lang en
```

[TVR-29 local evidence](evidence/tvr29-shadow-results.json) preserves pre-publication history: post-Show/TestBackend wide-glyph/cap/contrast regressions across 12 palettes, PTY input, external consumers and native static checks. Final release assets include RELEASE-MANIFEST.json and SHA256SUMS with source identity, main CI, public-tag consumers and downloaded binary validation. No CentOS, physical fonts/SSH or real application business integration checks. [Release files](https://github.com/leechis7/tuivory/releases/tag/go/v0.10.1).
