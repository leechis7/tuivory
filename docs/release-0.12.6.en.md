# Tuivory 0.12.6 release

[한국어 (기본)](release-0.12.6.md) · **English**

- [TVR-35](https://leechis7.atlassian.net/browse/TVR-35): The popup shadow can leave the top right cell untouched. The bottom corner stays connected across brighter backgrounds. [Shadow guide](popup-shadows.en.md)
- [TVR-36](https://leechis7.atlassian.net/browse/TVR-36): Front layers can block background input and cancel stale gestures. Go split panes send keys and paste to the focused pane. [Integration guide](layer-input.en.md)
- [TVR-37](https://leechis7.atlassian.net/browse/TVR-37): Workspace demos default to one tab row. Go and Rust offer `--tab-rows 3` to show the full outline. [Tab guide](workspace.en.md#tabs)

| Language | Installation |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.6` |
| Rust | Use Git tag `rust/v0.12.6` for the Cargo dependency or use the `.crate` source archive. |
| Python | `python -m pip install ./tuivory-0.12.6-py3-none-any.whl` |
| TypeScript/JavaScript | `npm install ./tuivory-0.12.6.tgz` |
| C | Extract the SDK and compile `src/tuivory.c` with `-Iinclude` into your application. |
| C++ | Extract the SDK, add `include/` to your build, and include `tuivory.hpp`. |
| Java | Add `tuivory-0.12.6.jar` to your classpath with JDK/JVM 17 or later. |

This release omits sample executables. [Source examples](examples.en.md) remain available in the repository. Run `sha256sum -c SHA256SUMS` to verify the downloaded packages.

[Installation](installation.en.md) · [Download the release](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.6)
