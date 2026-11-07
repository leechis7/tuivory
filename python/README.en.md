# Tuivory Python

[한국어 (기본)](README.md) · **English**

**Unreleased independent-language implementation. Not included in published 0.11.1.** No PyPI/npm/Maven/native SDK publication has occurred. The epic remains in progress.

All five languages provide installable/importable packages and independent Canvas, Tree/workspace, text/forms, collections, menus, feedback, layout, popups, documents, syntax and data grids. The epics remain in progress; drag-and-drop, terminal APIs and the remaining catalog are verified separately.

Implementations and runtimes are independent. No other Tuivory language implementation, FFI/JNI, subprocess engine or native bridge is required. Only design data/specifications/fixtures/build-time tools are shared. C++ does not call Tuivory C. TS emits JavaScript and declarations from one implementation.

Runtime / build: Python 3.11+; regex, wcwidth.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ./python
```

Commands run from the repository root unless shown otherwise. JavaScript users of the packed package need neither a TypeScript compiler nor a build step.

```sh
python3 -m tuivory --demo tree --lang en
```

Use `--snapshot` for noninteractive output and `--ascii`, `--theme`, `--colors` to select presentation. C/C++ Tree examples use w/s/a/d plus Enter; component examples use arrows and their displayed keys. Java uses command names followed by Enter and does not claim a raw-terminal adapter. Python/JS examples have opt-in terminal sessions; hosts otherwise own terminal lifecycle and global focus.

[Support/API/verification](../docs/languages.en.md) · [Examples](../docs/examples.en.md) · [TVR-15](https://leechis7.atlassian.net/browse/TVR-15)

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

[Independent data grid API](../docs/language-grid.en.md)
