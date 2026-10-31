# 공통 UI API 규칙

**한국어 (기본)** · [English](ui-facade.en.md)

0.8.0 TVR-26의 공통 UI 명세입니다. 현재 Go·Rust를 구현하며 Python·JavaScript/TypeScript·C·C++는 확장 대상으로 설계합니다. [언어별 API·전환](../docs/ui-facade.md)과 [입력/오프셋 시나리오](ui-input-cases.json)를 함께 유지합니다.

**0.8.0:** Go UI를 `github.com/leechis7/tuivory/go` 하나로 구성합니다. 기존 하위 경로는 호환용으로 유지합니다. [단일 import·이름 대응](../docs/ui-facade.md).

## 역할과 계층

| 계층 | 공통 규칙 | Go | Rust |
| --- | --- | --- | --- |
| 모델·이벤트 | 안정 ID, 원문, 선택, 상태, 요청 이벤트 | 루트 패키지 | collections/forms/text 등 |
| 컨트롤·표면·배치 | 그리기, 내부 조작, 크기 제약, 클리핑, 입력/모달 격리 | 루트 컴포넌트 View | ui::components 위젯 |
| 앱·위젯 호환 | 기존 SDK 내부 backend의 타입/메서드 정체성 보존 | 루트 (호환: go/ui) | ui의 Terminal/Frame 및 하위 모듈 |
| 터미널 호환 | 화면, 키·포인터, 스타일, 명시적 터미널 I/O | 루트 (호환: go/terminal) | ui::terminal, Session |
| 앱 정책 | 화면 구조, 컴포넌트 간 포커스 순서, 전역 키, DB·업무·클립보드 실행 | 앱 | 앱 |

기존 [컴포넌트 규칙](controls.md), [Tree](../docs/tree.md), [스타일](surfaces.md), [상태/포커스](../docs/focus.md), 메뉴·그림자 명세를 재사용합니다. 이 명세의 값은 특정 backend의 구조체나 수명 표현으로 정의하지 않습니다. 언어별 호환 별칭은 현재 backend를 교체해도 바이너리/소스가 그대로 호환된다는 약속이 아닙니다. 기존 API·메서드·trait는 유지하며 Go/Rust에 같은 함수 이름을 강제하지 않습니다.

## 공통 입력값

InputEvent는 kind와 선택적 key/text/modifiers/phase/x/y/button/width/height를 가집니다. JSON 시나리오는 의미 확인용이며 네트워크 프로토콜이나 C 메모리 배치를 정의하지 않습니다.

- kind: key, pointer, paste, resize, focus. 원점은 화면 왼쪽 위, 좌표/크기는 셀 단위입니다. 뷰 내부 좌표로 옮길 때 앱/컨테이너의 원점을 빼며 가상 영역은 스크롤을 더합니다.
- key: enter/escape/tab/backspace/delete/insert/left/right/up/down/home/end/page_up/page_down/f1… 또는 입력 문자. Ctrl 문자는 소문자 key와 ctrl modifier로 표현합니다.
- modifiers는 shift, ctrl, alt, meta 순서입니다. Rust Super/Meta는 meta로 표현합니다. raw text는 원래 UTF-8을 보존하며 붙여넣기 정규화는 편집 모델에서 수행합니다.
- key phase는 press/repeat/release. Go tcell의 키 이벤트는 press만 제공하며 키 반복은 연속 이벤트입니다. Rust도 단말이 제공한 phase만 알 수 있습니다. Tab/Ctrl+I, Enter/Ctrl+M처럼 단말에서 합쳐진 키는 복원할 수 없습니다.
- pointer phase는 down/up/move/drag/scroll_up/scroll_down/scroll_left/scroll_right. button은 left/right/middle/none. Go 위젯 이벤트의 click/double_click도 보존합니다. Rust raw 이벤트에서 클릭 횟수를 임의로 추측하지 않습니다. 단말이 제공하지 않은 이동/동시 버튼/포커스 이벤트를 만들어내지 않습니다.
- EditingAction은 Ctrl+A/C/X/Z/Y와 이동·선택·줄바꿈·스크롤·문자/붙여넣기를 편집 요청으로 바꿉니다. 키 release와 알려지지 않은 Ctrl 조합은 편집하지 않습니다. 폼은 Enter를 activate로 연결할 수 있습니다. 전역 키는 앱이 먼저 처리합니다.
- raw 입력값은 비밀 필드에 도달하기 전의 사용자 데이터입니다. 비밀값 보호는 모델의 마스킹·진단 투영에서 수행하며 라이브러리는 입력을 자동 기록하지 않습니다.

## 원문과 구문 강조

원문은 UTF-8이며 Cursor/Anchor/기본 SyntaxSpan은 grapheme 인덱스, 범위는 반열림입니다. GraphemeIndex/grapheme_index는 정확한 바이트 경계만 변환합니다. 결합 문자·CJK·이모지의 중간을 가리키면 오류입니다. SetByteSyntax/set_byte_syntax는 바이트 기반 렉서 결과를 한 번의 경계 인덱싱으로 변환하고 전체를 검증한 뒤 적용합니다. 실패 시 이전 강조를 보존합니다. SQL 해석·실행과 렉서 자체는 앱에 남습니다.

## 수명과 실행

Go 문자열/이벤트는 값이며 자식 컴포넌트는 동일 인스턴스를 연결합니다. Rust 원문 getter는 모델에 빌린 &str, 위젯은 그리기 범위의 참조를 사용합니다. 이벤트 콜백은 동기적이며 앱이 UI 실행 흐름에서 모델을 변경하거나 작업 결과를 큐로 전달합니다. SDK는 DB·인증·파일·클립보드 업무를 실행하지 않습니다.

터미널 수명은 앱이 명시적으로 선택합니다. Rust terminal 기능의 Session은 raw/대체 화면·마우스·붙여넣기 설정과 복원을 제공합니다. 중복 Session 진입과 다른 컨트롤러가 이미 소유한 raw 모드 진입은 오류이며 finish/Drop이 상태를 해제합니다. 초기화 실패와 panic unwind도 정리합니다. 프로세스 강제 종료/abort에는 Drop 실행을 보장하지 않습니다. Go Application은 기존 Run/Stop/SetScreen 수명과 콜백을 그대로 제공합니다. 전역 테마/테두리 설정은 이벤트 루프 시작 전에 setter로 적용합니다.

## 후속 언어와 호환성

| 언어 | 계획된 연결 방식 | 별도 결정/구현 |
| --- | --- | --- |
| Python | Python 패키지, 값/이벤트·모델 API, 언어별 터미널 어댑터 | Python 객체/버퍼 수명, 지원 런타임 |
| JS/TS | npm 패키지, 타입과 이벤트, 비동기 실행 흐름의 터미널 어댑터 | Node 런타임, Promise·작업 큐 연결 |
| C/C++ | opaque 모델 핸들·길이 지정 UTF-8 버퍼, 명시적 결과/해제, C++ RAII | ABI 버전, 정수 범위, 할당/해제 주체, 콜백·스레드 규칙 |

이들은 구현 완료가 아닙니다. FFI는 빌린 Rust 포인터나 Go 포인터를 공통 ABI로 직접 넘기지 않고 복사/명시적 소유권으로 연결하도록 설계합니다. 새 어댑터는 같은 ID·상태·입력·문자 폭·오프셋·배치 시나리오에 적합해야 합니다. 공통 모델 변경과 backend 호환 어댑터 변경을 구분해 문서화하며 Deprecated/제거는 [API 수명 정책](../docs/api-lifecycle.md)을 따릅니다.
