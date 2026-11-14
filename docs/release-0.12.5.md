# Tuivory 0.12.5 릴리스

**한국어 (기본)** · [English](release-0.12.5.en.md)

탭을 지원하는 일곱 SDK에서 탭 윤곽을 새로 그립니다. 두 줄 이상에서는 활성 탭 아래가 열려 본문과 이어집니다. 키보드 포커스는 별도로 표시하고 닫기 동작은 유지합니다. [탭 사용법과 화면](workspace.md#탭)

| 언어 | 설치 |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.5` |
| Rust | Cargo Git 의존성에 `rust/v0.12.5` 태그를 지정하거나 `.crate` 소스를 사용합니다. |
| Python | `python -m pip install ./tuivory-0.12.5-py3-none-any.whl` |
| TypeScript/JavaScript | `npm install ./tuivory-0.12.5.tgz` |
| C | SDK 압축을 풀고 `-Iinclude`를 지정해 `src/tuivory.c`를 앱과 함께 컴파일합니다. |
| C++ | SDK 압축을 풀고 `include/`를 빌드 경로에 추가한 뒤 `tuivory.hpp`를 포함합니다. |
| Java | JDK/JVM 17 이상에서 `tuivory-0.12.5.jar`를 클래스패스에 추가합니다. |

이번 릴리스에는 견본 실행파일을 포함하지 않습니다. [소스 예제](examples.md)는 저장소에서 사용할 수 있습니다. 다운로드한 패키지는 `sha256sum -c SHA256SUMS`로 확인합니다.

[설치 안내](installation.md) · [릴리스 다운로드](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.5)
