# Tuivory 0.12.2 release

[한국어 (기본)](release-0.12.2.md) · **English**

All seven grid implementations now use a dedicated background for the current cell in place of an underline. Dark and light 8-color profiles use blue for headers and the current cell and teal for selected ranges. The edited current cell keeps its asterisk, and other edited cells retain their edited background. [Grid examples](grid.en.md)

| Language | Installation or execution |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.2` |
| Rust | Use Git tag `rust/v0.12.2` in the Cargo dependency or use the `.crate` source archive. |
| Python | Install the downloaded wheel with `python -m pip install ./tuivory-0.12.2-py3-none-any.whl`. |
| TypeScript/JavaScript | Install the downloaded archive with `npm install ./tuivory-0.12.2.tgz`. |
| C and C++ | Extract the SDK for your architecture and use its headers and C static library. |
| Java | Add the JAR to your classpath with JDK/JVM 17 or later, or run `java -jar tuivory-0.12.2.jar --demo grid`. |

[Installation](installation.en.md) · [Verification record](evidence/tvr7-grid-current-cell-results.json)

GitHub provides native ARM64 and x86_64 static examples for Go, Rust, C, and C++, along with Python, TypeScript/JavaScript, and Java packages. Run `sha256sum -c SHA256SUMS` to verify the downloaded files. [Download the release](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.2)
