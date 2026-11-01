# Tuivory documentation

[한국어 (default)](README.md) · **English**

**0.9.1 TVR-27:** [Unified example executables](examples.en.md) provide one file per language, built only for the current Linux host architecture. Select examples with `--demo tree`, `--demo menu`, `--demo syntax`, etc.

**0.9.0 TVR-24:** [optional Oracle SQL/PLSQL analysis, common tokens and editor migration](syntax.en.md). Go uses one root import; Rust opts in with syntax-sql.

**0.9.1:** compose Go UI through `github.com/leechis7/tuivory/go` alone. Existing `/ui` and `/terminal` paths remain compatible. [Single import and name mappings](ui-facade.en.md).

Current release: **0.9.1**. Start with installation, choose a component, then consult its API.

- [Installation](installation.en.md)
- [Component guides](components.en.md)
- [API reference](api/README.en.md)
- [Design guide](design-guide.en.md)
- [Examples](examples.en.md)
- [Responsibilities](component-boundary.en.md)
- [Development and history](development.en.md)

[Current release](release-0.9.1.en.md)

0.7.0 TVR-26 adds SDK-only Go/Rust UI composition, shared input/byte-span conversion and terminal lifetime. [API mappings, examples and availability](ui-facade.en.md).
