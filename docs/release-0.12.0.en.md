# Tuivory 0.12.0 release

[한국어 (기본)](release-0.12.0.md) · **English**

This release includes independent Python, TypeScript/JavaScript, C, C++, and Java packages alongside Go and Rust. The new packages include trees, menus, forms, text editing, grids, drag and drop, and optional terminal sessions. See the [language API guide](languages.en.md) for availability and differences.

All implementations center each row of popup buttons after wrapping. Drawing and mouse hit testing use the same button rectangles. Rust also adds a Dialog model and a Ratatui widget. [Dialog APIs and examples](modals.en.md)

| Language | Installation or execution |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.0` |
| Rust | Use Git tag `rust/v0.12.0` in the Cargo dependency or use the `.crate` source archive. |
| Python | Install the downloaded wheel with `python -m pip install ./tuivory-0.12.0-py3-none-any.whl`. |
| TypeScript/JavaScript | Install the downloaded archive with `npm install ./tuivory-0.12.0.tgz`. |
| C and C++ | Extract the SDK for your architecture and use its headers and C static library. |
| Java | Add the JAR to your classpath with JDK/JVM 17 or later, or run `java -jar tuivory-0.12.0.jar --demo dialog`. |

Go, Rust, C, and C++ Linux examples are statically built on native ARM64 and x86_64 hosts. GitHub Release supplies the assets and their checksums. [Download the release](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.0)

[Changelog](../CHANGELOG.en.md) · [Installation](installation.en.md) · [Withdrawn versions](withdrawn-versions.en.md)
