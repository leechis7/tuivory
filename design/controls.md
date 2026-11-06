# Surface·컨트롤·텍스트·컨테이너 공통 명세

**한국어 (기본)** · [English](controls.en.md)

0.6.0 TVR-22~25의 언어 중립 규칙입니다. [사용법·API 대응](../docs/controls.md)과 [동일 시나리오](controls-cases.json)를 함께 유지합니다. Go/tview 또는 Rust/Ratatui 타입을 이 명세의 데이터 형식으로 강요하지 않습니다.

| 영역 | 규칙 |
| --- | --- |
| 표면 | 먼저 불투명 표면을 채우고 자식을 그림. 기본 테두리/여백 0. 두 칸 문자가 경계를 걸치면 전체 grapheme을 정리하고 바깥 스타일 보존 |
| 입력 | 안정 ID·독립 상태를 사용. disabled는 조작 차단, busy는 수정/실행 차단, readonly는 선택/복사 허용 |
| 비밀 | 원문 조회는 명시적 호출. 모델의 표시/진단 투영과 copy/cut에는 비밀 원문을 포함하지 않음 |
| 텍스트 | 논리 원문은 UTF-8. Cursor/Anchor/스타일 범위는 확장 grapheme 인덱스. 범위는 반열림. 셀 좌표와 byte offset은 별도 변환 |
| 편집 | 선택 교체·Undo/Redo 최근 128회. paste는 LF/공백으로 정규화. 읽기 전용과 disabled의 편집은 무효 |
| 마크업 | 기본 literal. 명시적으로 [role]text[/], [[ 이스케이프를 파싱. 알 수 없는/불균형 태그는 변경 전 오류 |
| 배치 | row/column/grid/layers, 안정 자식 ID, 트랙 min/max/fixed/weight·span·padding/gap. 작은 영역은 간격 제거 후 앞에서부터 축소 |
| 상태 | resize/reflow/팔레트 변경은 원문·선택·스크롤·살아 있는 포커스 ID를 재생성하지 않음 |
| 레이어 | 뒤에 선언한 레이어가 위. 마지막 보이는 모달 아래 입력 금지. 드래그는 캡처 ID로 전달하고 제거 시 해제. 닫을 때 호출 ID 복귀 |
| 오류 | 잘못된 필드/옵션/ID/범위/역할은 error/Result. 실패한 setter는 원자적이며 이전 상태 보존 |
| 이벤트 | change/select/activate/submit/cancel/copy/cut는 호스트 요청. DB·SQL·인증·클립보드·파일 I/O 없음 |

렌더링 장식은 Unicode/ASCII와 12팔레트를 따릅니다. ASCII 모드여도 사용자 원문을 음역/변형하지 않습니다. 셀 안에 반쪽 grapheme을 만들지 않습니다. 원문에 대한 클릭/스크롤은 뷰포트 셀 좌표에서 변환합니다. 렌더러의 가상 캔버스 한도는 축 65,535셀, 총 1,000,000셀입니다. 순수 배치 계산의 축 값은 최대 1,000,000, 항목/트랙은 최대 1,024입니다. Go의 음수 화면 좌표는 내부 클리핑에 사용할 수 있으며 공유 시나리오의 논리 사각형은 비음수입니다.

현재 적합성 구현은 Go·Rust입니다. 향후 Python·JavaScript/TypeScript·C·C++는 동일 의미의 자연스러운 API/바인딩을 연결할 수 있도록 안정 ID·값/이벤트·오프셋 단위를 유지합니다. 그 구현과 ABI/메모리 소유권·전체 backend facade는 후속 작업이며 여기서 제공한 것으로 보지 않습니다.

## 값과 수명

원문·선택·Undo 이력은 모델이 소유하며 렌더링마다 재생성하지 않습니다. 이벤트의 문자열은 전달된 값이며 클립보드/저장을 자동 실행하지 않습니다. Go의 원문 조회는 불변 string 값이고 Rust는 모델에 빌린 &str을 반환합니다. Rust의 위젯·Styles 참조는 그리기 호출 범위에서 빌리며 모델 변경에 필요한 &mut 참조와 함께 Rust 수명 규칙을 따릅니다. Go Container 생성자와 SetOptions/SetChildren은 설정 목록을 복사하지만 자식 컴포넌트는 같은 인스턴스를 연결합니다. 렌더러 콜백은 동기적으로 호출합니다. 이 규칙은 언어 간 의미를 맞추기 위한 것이며 공통 C ABI나 메모리 배치를 정의하지 않습니다.

0.7.0 TVR-26: Go·Rust에서 Tuivory 경로만 사용하는 UI 구성, 공통 입력·바이트 span 변환과 터미널 수명을 제공합니다. [API 대응·예제·현재 제공 상태](../docs/ui-facade.md).

## TVR-7 그리드 데이터 작업 (0.11.0)

기존 그리드 모델·렌더러를 재사용합니다. 선택적 셀 내 편집은 버퍼·grapheme 커서/마우스·클리핑·내부 포커스를 관리합니다. 호스트가 허용 여부/초깃값을 공급하고 제출 승인·소스 변경·트랜잭션을 담당합니다. 요청 ID와 소스/문맥 세대로 늦은 응답·중복 승인을 거부합니다. 열 고정/숨김/순서/보기 상태는 안정 ID를 사용하고 좁은 화면의 고정/일반 영역은 겹치지 않습니다. 변경 셀은 선택/비활성/오류가 겹쳐도 `*`를 유지하며 행 Edited/집계 콜백은 행 번호 표식만 제어합니다. 12팔레트와 Unicode/ASCII에 기존 의미 역할을 사용하고 grid.match는 warning에서 파생합니다. 인용 TSV는 제한된 전체 묶음으로 검증하며 직접 적용하지 않습니다. 찾기는 공급된 소스만 제한 내에서 검사하고 전체 검색·저장은 호스트 요청입니다. 상세 보기는 원문 읽기 전용 뷰어입니다.

[API·우선순위·제한](../docs/grid-workspace.md) · [공유 TSV 사례](grid-work-cases.json) · [근거](../docs/evidence/tvr7-grid-workspace-results.json).

## 그리드 실제 커서 (0.11.1)

편집 버퍼에 가짜 커서 문자를 넣지 않습니다. 텍스트·마우스·로컬 커서가 같은 grapheme 뷰포트를 사용합니다. 포커스 뷰는 위치·가시성만 소유하며 NULL·승인 대기·클리핑·무효화·포커스 해제 때 오래된 커서를 숨깁니다. Go는 NewGridView와 NewCursorScreen/PreserveCursorTty로 backend 기본 모양·깜빡임 명령을 제거합니다. Rust는 GridWidget::render_frame을 사용하고 버퍼 전용 Widget은 실제 커서를 등록하지 않습니다. 전역 포커스·레이어 선택은 앱 책임입니다. [연결·근거](../docs/grid-workspace.md).

[독립 언어 workspace API·예제](../docs/language-workspace.md): 탭·패널·분할·경로·상태줄을 다섯 구현에서 검증했습니다. 나머지 카탈로그 이식은 진행 중입니다.

[독립 언어 입력·편집 API](../docs/language-text.md)

[독립 언어 폼·컨트롤 API](../docs/language-forms.md)
