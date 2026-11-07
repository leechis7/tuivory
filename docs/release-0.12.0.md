# Tuivory 0.12.0 릴리스

**한국어 (기본)** · [English](release-0.12.0.en.md)

Go·Rust와 함께 Python·TypeScript/JavaScript·C·C++·Java 독립 패키지를 제공합니다. 새 패키지에는 트리, 메뉴, 폼, 텍스트 편집, 그리드, 드래그앤드롭 및 선택적 터미널 세션이 포함됩니다. 지원 범위와 언어별 차이는 [언어별 API 안내](languages.md)에서 확인할 수 있습니다.

모든 구현은 팝업 버튼이 줄바꿈된 뒤 각 행을 가운데 정렬합니다. 그리기와 마우스 판정에 같은 버튼 사각형을 사용합니다. Rust에는 Dialog 모델과 Ratatui 위젯도 추가했습니다. [확인창 API와 예제](modals.md)

| 언어 | 설치·실행 |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.0` |
| Rust | Cargo Git 의존성에 `rust/v0.12.0` 태그를 지정하거나 `.crate` 소스를 사용합니다. |
| Python | 다운로드한 휠을 `python -m pip install ./tuivory-0.12.0-py3-none-any.whl`로 설치합니다. |
| TypeScript/JavaScript | 다운로드한 패키지를 `npm install ./tuivory-0.12.0.tgz`로 설치합니다. |
| C·C++ | 호스트 아키텍처에 맞는 SDK를 풀고 헤더와 정적 라이브러리(C)를 사용합니다. |
| Java | JDK/JVM 17 이상에서 JAR을 클래스패스에 추가하거나 `java -jar tuivory-0.12.0.jar --demo dialog`로 예제를 실행합니다. |

Go·Rust·C·C++ Linux 예제는 ARM64와 x86_64 네이티브 호스트에서 정적으로 빌드합니다. GitHub Release에서 파일과 체크섬을 받을 수 있습니다. [릴리스 다운로드](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.0)

[변경 이력](../CHANGELOG.md) · [설치 안내](installation.md) · [회수 버전](withdrawn-versions.md)
