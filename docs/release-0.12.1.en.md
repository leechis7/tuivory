# Tuivory 0.12.1 release

[한국어 (기본)](release-0.12.1.md) · **English**

All seven implementations use a dedicated grid header color. Column labels, dividers, and trailing space share one background. The dark theme uses slate blue, the light theme uses pale blue, and monochrome uses inverse colors. The dark and light themes use purple in the 8- and 16-color profiles. [Grid screenshots](grid.en.md)

| Language | Installation or execution |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.1` |
| Rust | Use Git tag `rust/v0.12.1` in the Cargo dependency or use the `.crate` source archive. |
| Python | Install the downloaded wheel with `python -m pip install ./tuivory-0.12.1-py3-none-any.whl`. |
| TypeScript/JavaScript | Install the downloaded archive with `npm install ./tuivory-0.12.1.tgz`. |
| C and C++ | Extract the SDK for your architecture and use its headers and C static library. |
| Java | Add the JAR to your classpath with JDK/JVM 17 or later, or run `java -jar tuivory-0.12.1.jar --demo dialog`. |

[Installation](installation.en.md) · [Verification record](evidence/tvr7-grid-header-results.json)

GitHub provides native ARM64 and x86_64 static examples for Go, Rust, C, and C++, along with Python, TypeScript/JavaScript, and Java packages. Run `sha256sum -c SHA256SUMS` to verify the downloaded files. [Download the release](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.1)
