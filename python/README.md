# Tuivory Python

**한국어 (기본)** · [English](README.en.md)

**미배포 독립 언어 구현입니다. 기존 공개 0.11.1에는 포함되지 않습니다.** PyPI/npm/Maven/네이티브 SDK 게시는 수행하지 않았으며 에픽은 진행 중입니다.

첫 검증 단위는 실제 설치·import/include 가능한 패키지, 내장 팔레트·의미별 상태·셀 버퍼와 Tree입니다. Python/TS에는 후속 컴포넌트 초안도 있으나 Go/Rust 전체 기능 이식 완료를 의미하지 않습니다.

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

비대화형 출력은 `--snapshot`, 표현 선택은 `--ascii`·`--theme`·`--colors`를 사용합니다. C/C++ 예제는 w/s/a/d와 Enter를 사용합니다. Java 예제는 명령어 입력 후 Enter를 누르는 줄 입력 방식이며 raw 터미널 어댑터를 제공한다고 주장하지 않습니다. Python/JS 예제는 명시적으로 터미널 모드에 진입하며 그 밖의 단말 수명과 전역 포커스는 앱 책임입니다.

[Support/API/verification](../docs/languages.md) · [Examples](../docs/examples.md) · [TVR-15](https://leechis7.atlassian.net/browse/TVR-15)

[Workspace 후속](../docs/language-workspace.md): `--demo workspace`로 검증한 탭·패널·분할·경로·상태줄을 실행합니다.

[독립 언어 입력·편집 API](../docs/language-text.md)

[독립 언어 폼·컨트롤 API](../docs/language-forms.md)

[독립 언어 포커스 범위 API](../docs/language-focus.md)

[독립 언어 목록·검색 선택기 API](../docs/language-collections.md)

[독립 언어 메뉴·문맥 메뉴 API](../docs/language-menu.md)

[독립 언어 알림·진행·데이터 상태 API](../docs/language-feedback.md)

[독립 언어 간격·스택·배지·칩·단축키 안내 API](../docs/language-layout.md)

[독립 언어 컨테이너·셀 복사 API](../docs/language-containers.md)
