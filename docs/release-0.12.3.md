# Tuivory 0.12.3 릴리스

**한국어 (기본)** · [English](release-0.12.3.en.md)

일곱 언어 구현의 분할창에 지정 패널을 접고 펼치는 기능을 추가했습니다. 다시 펼치면 현재 창 크기와 패널 최소 크기를 반영해 이전 비율을 복원합니다. Go·Rust 예제에서는 분할선을 클릭하거나 F7을 누릅니다. [분할창 API와 예제](workspace.md)

| 언어 | 설치·실행 |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.3` |
| Rust | Cargo Git 의존성에 `rust/v0.12.3` 태그를 지정하거나 `.crate` 소스를 사용합니다. |
| Python | 다운로드한 휠을 `python -m pip install ./tuivory-0.12.3-py3-none-any.whl`로 설치합니다. |
| TypeScript/JavaScript | 다운로드한 패키지를 `npm install ./tuivory-0.12.3.tgz`로 설치합니다. |
| C·C++ | 호스트 아키텍처에 맞는 SDK를 풀고 헤더와 정적 라이브러리(C)를 사용합니다. |
| Java | JDK/JVM 17 이상에서 JAR을 클래스패스에 추가하거나 `java -jar tuivory-0.12.3.jar --demo workspace`로 예제를 실행합니다. |

[설치 안내](installation.md) · [검증 기록](evidence/tvr33-split-collapse-results.json)

Go·Rust·C·C++의 ARM64 및 x86_64 정적 예제와 Python·TypeScript/JavaScript·Java 패키지는 GitHub에서 받을 수 있습니다. 다운로드한 파일은 `sha256sum -c SHA256SUMS`로 확인합니다. [릴리스 다운로드](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.3)
