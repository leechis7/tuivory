# Tuivory 0.12.3 release

[한국어 (기본)](release-0.12.3.md) · **English**

All seven SDKs now support collapsing a chosen split panel and restoring its previous ratio within the current terminal size and panel minima. In the Go and Rust examples, click the divider or press F7. [Split API and examples](workspace.en.md)

| Language | Installation or execution |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.3` |
| Rust | Use Git tag `rust/v0.12.3` in the Cargo dependency or use the `.crate` source archive. |
| Python | Install the downloaded wheel with `python -m pip install ./tuivory-0.12.3-py3-none-any.whl`. |
| TypeScript/JavaScript | Install the downloaded archive with `npm install ./tuivory-0.12.3.tgz`. |
| C and C++ | Extract the SDK for your architecture and use its headers and C static library. |
| Java | Add the JAR to your classpath with JDK/JVM 17 or later, or run `java -jar tuivory-0.12.3.jar --demo workspace`. |

[Installation](installation.en.md) · [Verification record](evidence/tvr33-split-collapse-results.json)

GitHub provides native ARM64 and x86_64 static examples for Go, Rust, C, and C++, along with Python, TypeScript/JavaScript, and Java packages. Run `sha256sum -c SHA256SUMS` to verify the downloaded files. [Download the release](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.3)
