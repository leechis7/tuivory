# Origin and license

[한국어 (default)](NOTICE.md) · **English**

Copyright (C) 2026 Chaekang Lee

Initial documentation, theme examples, and terminal color samples derive from [LazyOra](https://github.com/leechis7/lazyora) work item LORA-69. Developer: Chaekang Lee (이채강), leechis7@gmail.com.

Source baseline: [a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7](https://github.com/leechis7/lazyora/commit/a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7).

Documentation links and project boundaries were reorganized for an independent repository, with reference palette validation tools added. Existing AGPL-3.0-only terms are preserved; no arbitrary relicensing occurred. See [LICENSE](LICENSE) for the full terms.

Official references are linked in [sources](docs/sources.en.md). Full documentation or implementation libraries from Textual, Lip Gloss, Ratatui, Carbon, W3C, and others are not bundled; names identify sources.

The runnable playground uses stock tview/tcell through Go modules, without LazyOra's local tview fork. The overlap handling for dropdowns covering existing two-cell Korean glyphs adapts the LazyOra case. Dependency versions are recorded in go/go.mod and go/go.sum.

The Go package derives from LazyOra's actual theme/style functions. Source commits, file hashes, and extraction scope are preserved in the [extraction record](docs/lazyora-extraction.en.md), under the existing AGPL-3.0-only terms.

## Tuivory origin

Tuivory began in a new repository based on the implementation and language-neutral restructuring work from [TUIS](https://github.com/leechis7/tuis). Existing copyright, AGPL-3.0-only terms, and LazyOra style attribution are preserved. See [installation and usage](docs/installation.en.md) for current usage. This is an origin notice, not the current product name, package, or work-tracking convention.
