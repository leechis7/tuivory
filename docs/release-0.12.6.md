# Tuivory 0.12.6 릴리스

**한국어 (기본)** · [English](release-0.12.6.en.md)

- [TVR-35](https://leechis7.atlassian.net/browse/TVR-35): 팝업 오른쪽 그림자의 맨 위 칸을 비울 수 있고, 밝은 배경에서도 아래 모서리가 이어집니다. [그림자 안내](popup-shadows.md)
- [TVR-36](https://leechis7.atlassian.net/browse/TVR-36): 전면 레이어가 뒤쪽 입력을 차단하고 이전 제스처를 취소할 수 있습니다. Go 분할창의 키·붙여넣기는 실제 포커스를 따릅니다. [적용 안내](layer-input.md)
- [TVR-37](https://leechis7.atlassian.net/browse/TVR-37): 작업 공간 예제의 탭은 기본 한 줄입니다. Go·Rust 예제에서 `--tab-rows 3`으로 세 줄을 선택할 수 있습니다. [탭 안내](workspace.md#탭)

| 언어 | 설치 |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.6` |
| Rust | Cargo Git 의존성에 `rust/v0.12.6` 태그를 지정하거나 `.crate` 소스를 사용합니다. |
| Python | `python -m pip install ./tuivory-0.12.6-py3-none-any.whl` |
| TypeScript/JavaScript | `npm install ./tuivory-0.12.6.tgz` |
| C | SDK 압축을 풀고 `-Iinclude`를 지정해 `src/tuivory.c`를 앱과 함께 컴파일합니다. |
| C++ | SDK 압축을 풀고 `include/`를 빌드 경로에 추가한 뒤 `tuivory.hpp`를 포함합니다. |
| Java | JDK/JVM 17 이상에서 `tuivory-0.12.6.jar`를 클래스패스에 추가합니다. |

이번 릴리스에는 견본 실행파일을 포함하지 않습니다. [소스 예제](examples.md)는 저장소에서 사용할 수 있습니다. 다운로드한 패키지는 `sha256sum -c SHA256SUMS`로 확인합니다.

[설치 안내](installation.md) · [릴리스 다운로드](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.6)
