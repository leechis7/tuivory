# Tuivory C++

[한국어 (기본)](README.md) · **English**

**Unreleased independent-language implementation. Not included in published 0.11.1.** No PyPI/npm/Maven/native SDK publication has occurred. The epic remains in progress.

First verification unit: an installable/importable package, embedded palettes, semantic states, cell buffer and Tree. Python/TS also contain follow-up component prototypes; these do not establish full Go/Rust feature parity.

Implementations and runtimes are independent. No other Tuivory language implementation, FFI/JNI, subprocess engine or native bridge is required. Only design data/specifications/fixtures/build-time tools are shared. C++ does not call Tuivory C. TS emits JavaScript and declarations from one implementation.

Runtime / build: C++17 compiler (build time); statically linked standard library.

```sh
make build-cpp
```

Commands run from the repository root unless shown otherwise. JavaScript users of the packed package need neither a TypeScript compiler nor a build step.

```sh
./bin/cpp/tuivory-linux-<arch> --demo tree --lang en
```

Use `--snapshot` for noninteractive output and `--ascii`, `--theme`, `--colors` to select presentation. C/C++ examples use w/s/a/d plus Enter. Java uses command names followed by Enter and does not claim a raw-terminal adapter. Python/JS examples have opt-in terminal sessions; hosts otherwise own terminal lifecycle and global focus.

[Support/API/verification](../docs/languages.en.md) · [Examples](../docs/examples.en.md) · [TVR-31](https://leechis7.atlassian.net/browse/TVR-31)

[Workspace follow-up](../docs/language-workspace.en.md): select `--demo workspace` for validated tabs, panels, splits, breadcrumbs and status lines.

[Independent text editing API](../docs/language-text.en.md)

[Independent forms and controls API](../docs/language-forms.en.md)

[Independent focus scope API](../docs/language-focus.en.md)

[Independent lists and search pickers API](../docs/language-collections.en.md)

[Independent menu/context-menu API](../docs/language-menu.en.md)

[Independent notices/progress/data-state API](../docs/language-feedback.en.md)

[Independent spacing/stack and badge/chip/hint API](../docs/language-layout.en.md)

[Independent containers and cell-copy API](../docs/language-containers.en.md)

[Independent Surface and background API](../docs/language-surfaces.en.md)

[Independent popup shadows and dialogs](../docs/language-popups.en.md)

[Independent document viewing/editing API](../docs/language-documents.en.md)

[Independent syntax highlighting/SQL classification API](../docs/language-syntax.en.md)
