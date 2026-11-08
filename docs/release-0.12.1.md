# Tuivory 0.12.1 릴리스

**한국어 (기본)** · [English](release-0.12.1.en.md)

일곱 언어 구현에 그리드 헤더 전용 색을 추가했습니다. 열 이름, 구분선, 오른쪽 빈칸까지 한 줄로 이어집니다. 다크는 청회색, 라이트는 옅은 청색, 흑백은 반전으로 구분합니다. 다크와 라이트의 8·16색 프로필은 보라색을 사용합니다. [그리드 예제 화면](grid.md)

| 언어 | 설치·실행 |
| --- | --- |
| Go | `go get github.com/leechis7/tuivory/go@v0.12.1` |
| Rust | Cargo Git 의존성에 `rust/v0.12.1` 태그를 지정하거나 `.crate` 소스를 사용합니다. |
| Python | 다운로드한 휠을 `python -m pip install ./tuivory-0.12.1-py3-none-any.whl`로 설치합니다. |
| TypeScript/JavaScript | 다운로드한 패키지를 `npm install ./tuivory-0.12.1.tgz`로 설치합니다. |
| C·C++ | 호스트 아키텍처에 맞는 SDK를 풀고 헤더와 정적 라이브러리(C)를 사용합니다. |
| Java | JDK/JVM 17 이상에서 JAR을 클래스패스에 추가하거나 `java -jar tuivory-0.12.1.jar --demo dialog`로 예제를 실행합니다. |

[설치 안내](installation.md) · [검증 기록](evidence/tvr7-grid-header-results.json)

Go·Rust·C·C++의 ARM64 및 x86_64 정적 예제와 Python·TypeScript/JavaScript·Java 패키지는 GitHub에서 받을 수 있습니다. 다운로드한 파일은 `sha256sum -c SHA256SUMS`로 확인합니다. [릴리스 다운로드](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.1)
