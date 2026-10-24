# Roadmap

[한국어 (default)](roadmap.md) · **English**

## Product goal

Provide a TUI style package that applications import. Go `v0.0.1` is published; current work maintains Go usability and parity with its source styles and validates actual LazyOra imports. Documentation, specifications, and templates support package use and validation. Other language UI packages remain future work. The direction is shared rules, reusable implementations, and a catalog, similar in purpose to Bootstrap, Tailwind CSS, or MUI; web CSS is not applied directly to terminals.

Current priorities are Go source parity and actual LazyOra integration. Other language UI implementations follow later.

The root uses the language-neutral `design/docs/go/python/javascript/shell/examples` layout. Go is a submodule at `github.com/leechis7/tuivory/go`; its first release is 0.0.1.

## Implemented today

- [Shared specification](../design/README.en.md): semantic roles, terminal profiles, component state, input, and cell layout contracts.
- [Shared tokens](../design/tokens/README.en.md): draft JSON and schema, 12 palettes and 192 reference pairs.
- [Go package](lazyora-extraction.en.md): styles extracted from LazyOra, stock tview application methods, starter template, framework-independent candidate token loader.
- [Go playground](playground.en.md): inputs, choices, tables, popups, and theme-change state preservation.
- Python and Node.js token reading examples and comparison with Go.
- Palette calculations, local link checks, and a real terminal evidence template.

The Go package is released as `v0.0.1`. This does not mean a complete multi-language widget SDK or Python/JavaScript/Shell UI packages are available. Korean/English playground selection and English reference images are merged into `main` without a new version tag.

## Next steps

1. Validate the public Go API and application boundaries through LazyOra's style adapter.
2. Implement inputs, buttons, lists, and modals in one Python or JavaScript framework to test reuse of the specification.
3. Organize Shell ANSI templates, extract validated reusable components, and extend spacing, border, and state tokens.
4. Expand the catalog to connect language examples, support scope, and evidence.
5. Collect real terminal observations and define package naming, distribution, and compatibility policies.

Keep calculations, simulations, and actual SecureCRT/MobaXterm/xterm-compatible terminal results separate. Input I/O, capability detection, and database drivers stay outside the shared core; link to application examples at their source.

Future stages use separate issues. The maintainer decides product major and stable versions. Commits and GitHub publication require explicit approval.
