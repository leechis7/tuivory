# Validation evidence

[한국어 (default)](README.md) · **English**

Distinguish calculations, simulations, and actual terminal observations. Mark unverified items as unverified. Use synthetic data instead of actual hostnames, accounts, passwords, or business data.

```text
Rule/component ID:
Guide/theme/adapter version or commit:
Application/widget version, OS/architecture:
Theme, profile, TERM/COLORTERM, library-reported color count:
Terminal/version, local/SSH/tmux path:
ANSI palette (reference/custom/unverified), bold settings:
Window size (columns×rows), font, language:
Initial state and reproduction steps:
Expected / actual result:
Method: palette calculation / widget simulation / actual terminal
Result: pass / fail / unverified, exceptions:
Evidence location, observation date:
```

## Initial case: LazyOra LORA-69

[Investigation](https://github.com/leechis7/lazyora/blob/a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7/docs/audits/lora-69.md) · [Implementation and validation](https://github.com/leechis7/lazyora/blob/a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7/docs/audits/lora-69-implementation.md)

The case compared 67 scenes × 12 combinations × Korean/English × initial/round-trip: 3,216 frames rendered from actual application widgets through tcell simulation. General rules came from theme restoration broken by value substitution, form input colors hiding read-only descriptions, and ANSI Bold reducing selected-cell contrast.

Oracle data types, workers, and database test infrastructure are not copied here. The application-specific capture harness stays in LazyOra. Tuivory provides its own independent playground and bilingual SVG generation through the [playground guide](../docs/playground.en.md), plus executable checks in `tools/smoke_playground.py`. Use the template above for general observations. The LazyOra case is not evidence of actual SecureCRT/MobaXterm user palettes.

## Static distribution

[Go/Rust/CentOS 7.4 validation](static-build.en.md): actual legacy guest kernel, external static hosts, bilingual UI and local ARM64 checks.

## Shared control states, focus and popups

[TVR-8 validation](focus.en.md): shared specifications, twelve palettes, localized PTYs, external static hosts, CentOS 7.4 and localized references. Local validation before publication; remote publication/CI results are recorded separately in TVR-8 comments.

[TVR-9–13 component validation](components.en.md): public APIs, row sources, requests/lifetimes, geometry, localized PTYs and static external hosts.

[TVR-14 overlay boundary validation](overlay-drawing.en.md): shared Go API, actual widgets, output after Show, external static imports, PTYs and limitations.

[0.2.0 release preparation validation](release-0.2.0.en.md): candidate assets, versions/checksums, static builds, external installation and native/legacy-kernel execution.
