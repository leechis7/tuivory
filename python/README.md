# Tuivory Python

**한국어 (기본)** · [English](README.en.md)

GitHub Release에서 0.12.1 패키지를 제공합니다. 다운로드와 설치 방법은 [릴리스 안내](../docs/release-0.12.1.md)를 참고합니다.

다섯 언어는 설치·import/include 가능한 패키지와 독립 캔버스, Tree·작업 영역·입력·폼·목록·메뉴·알림·배치·팝업·문서·구문 강조·데이터 그리드·드래그앤드롭·입력 해석과 선택적 터미널 API를 제공합니다. 그리드는 [포인터와 범위 선택](../docs/language-grid.md)을 제공합니다. 에픽은 열린 상태입니다.

구현과 런타임은 언어별로 독립적입니다. 다른 Tuivory 언어 구현·FFI/JNI·서브프로세스 엔진·네이티브 연결을 요구하지 않습니다. 디자인 데이터·명세·테스트 사례·개발 도구만 공유합니다. C++도 Tuivory C를 호출하지 않으며 TS는 한 구현에서 JavaScript와 타입 선언을 생성합니다.

런타임·빌드: Python 3.11+; regex, wcwidth.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ./python
```

별도 표시가 없으면 저장소 루트 기준입니다. 빌드된 npm 패키지를 사용하는 JavaScript 앱에는 TypeScript 컴파일러나 빌드 과정이 필요 없습니다.

```sh
python3 -m tuivory --demo tree --lang ko
```

비대화형 출력은 `--snapshot`, 표현 선택은 `--ascii`·`--theme`·`--colors`를 사용합니다. C/C++ Tree 예제는 w/s/a/d와 Enter를 사용하고, 컴포넌트 예제는 방향키와 화면에 표시한 키를 사용합니다. Java 기본 예제는 명령어 입력 후 Enter를 누르는 줄 입력 방식입니다. 앱은 별도로 제공하는 POSIX raw 세션을 선택할 수 있으며 OS stty와 /dev/tty가 필요합니다. Python/JS 예제는 명시적으로 터미널 모드에 진입하며 그 밖의 단말 수명과 전역 포커스는 앱 책임입니다.

[Support/API/verification](../docs/languages.md) · [Examples](../docs/examples.md) · [TVR-15](https://leechis7.atlassian.net/browse/TVR-15)
