# Tuivory C

[한국어 (기본)](README.md) · **English**

**Unreleased independent-language implementation. Not included in published 0.11.1.** No PyPI/npm/Maven/native SDK publication has occurred. The epic remains in progress.

All five languages provide installable/importable packages and independent Canvas, Tree/workspace, text/forms, collections, menus, feedback, layout, popups, documents, syntax, data grids, drag and drop, input decoding and optional terminal APIs. The epics remain in progress; additional grid pointer behavior and full catalog parity remain under verification.

Implementations and runtimes are independent. No other Tuivory language implementation, FFI/JNI, subprocess engine or native bridge is required. Only design data/specifications/fixtures/build-time tools are shared. C++ does not call Tuivory C. TS emits JavaScript and declarations from one implementation.

Runtime / build: C11 compiler + ar (build time); no language runtime.

```sh
make build-c
```

Commands run from the repository root unless shown otherwise.

```sh
./bin/c/tuivory-linux-<arch> --demo tree --lang en
```

Use `--snapshot` for noninteractive output and `--ascii`, `--theme`, `--colors` to select presentation. C/C++ Tree examples use w/s/a/d plus Enter; component examples use arrows and their displayed keys. The default Java example uses command names followed by Enter. Applications may opt into the provided POSIX raw session, which requires OS stty and /dev/tty. Python/JS examples have opt-in terminal sessions; hosts otherwise own terminal lifecycle and global focus.

[Support/API/verification](../docs/languages.en.md) · [Examples](../docs/examples.en.md) · [TVR-30](https://leechis7.atlassian.net/browse/TVR-30)
