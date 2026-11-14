# Tuivory 0.12.5 release

[한국어 (기본)](release-0.12.5.md) · **English**

All seven SDKs with tabs now draw an outline. With at least two rows, the active tab opens into the content below. Keyboard focus remains separate and close behavior is unchanged. [Tab guide and screenshots](workspace.en.md#tabs)

| Language | Installation |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.5` |
| Rust | Use Git tag `rust/v0.12.5` for the Cargo dependency or use the `.crate` source archive. |
| Python | `python -m pip install ./tuivory-0.12.5-py3-none-any.whl` |
| TypeScript/JavaScript | `npm install ./tuivory-0.12.5.tgz` |
| C | Extract the SDK and compile `src/tuivory.c` with `-Iinclude` into your application. |
| C++ | Extract the SDK, add `include/` to your build, and include `tuivory.hpp`. |
| Java | Add `tuivory-0.12.5.jar` to your classpath with JDK/JVM 17 or later. |

This release omits sample executables. [Source examples](examples.en.md) remain available in the repository. Run `sha256sum -c SHA256SUMS` to verify the downloaded packages.

[Installation](installation.en.md) · [Download the release](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.5)
