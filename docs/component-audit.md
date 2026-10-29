# 공통 UI 지원 범위 점검 — TVR-7

**한국어 (기본)** · [English](component-audit.en.md)

2026-10-29의 v0.2.0 배포와 TVR-17 로컬 커밋 `e34b824`를 구분해 재점검했습니다. 책임 범위·그리드 옵션·공통 메뉴는 dev에 통합했고 0.3.0에 포함합니다. 에픽은 열린 상태를 유지합니다. 아래 현재 범위가 우선이며 2026-10-27 표는 시작 시점 기록입니다. [책임 범위](component-boundary.md).

## 현재 지원과 앱 책임

| 영역 | Go / Rust 공개 제공 | 미제공 또는 앱 책임 |
| --- | --- | --- |
| 입력·폼 | Form 모델·렌더러, 입력/선택·필수 값·제출 요청 | 접속/설정 화면 조합·업무 검증·저장 |
| 트리 | NewTree/TreeState/NewTreeView / tree::Tree/TreeState/TreeWidget | 실제 데이터·로딩·항목 실행 |
| 메뉴·검색 | NewList/NewSearchPicker / collections::ListModel/SearchPicker, 평면 항목·필터·선택 요청 | v0.2.0은 평면 목록. 0.3.0 Menu/NewMenuView 및 menu::Menu/MenuPopupWidget은 계층·복귀·바·단일 팝업 제공. 메뉴 내용·원격 후보 생성은 앱 책임 |
| 탭 | Tabs/TabState/NewTabView / components::Tabs/TabState/TabsWidget, 넘침·변경·닫기 요청 | SQL/세션 소유권·문서 저장·닫기 승인 |
| 패널·분할 | NewPanelView/NewSplitView / Styles::panel/split_rects, 할당 영역 안의 크기 계산 | 화면별 위치·방향·초기 크기·가시성·반응형 구성 선택 |
| 포커스·팝업 | FocusStack, 호스트 정의 스코프의 탐색·차단·복귀 | 컴포넌트 사이 순서·스코프 등록·단말 이벤트 연결 |
| 상태·경로·도움말 | StatusLine/Breadcrumbs/Help와 각 언어 렌더러 | 상황별 항목·명령/키 배정·도움말 화면/목차 |
| 그리드 | v0.2.0 Grid/GridSource·기본 렌더러. TVR-17 옵션/범위/상태줄은 0.3.0에 포함 | 실제 조회·업무 편집·트랜잭션·클립보드/내보내기 |
| 테마·검증 | 공통 토큰·의미별 스타일·상태 보존·문자 폭/정적 배포 검사 | 실제 적용 앱/고객 단말 검증은 별도. Go 추출 스타일 전체와 Rust 후보 팔레트의 동등성을 주장하지 않음 |

책임 범위 점검 후 사용자가 메뉴 개선을 지시해 [공통 Menu](menus.md)를 TVR-7의 0.3.0 기능으로 추가했습니다. 공개 0.2.0과 새 구현을 구분하며 명령 분류·실행은 앱 책임입니다. 탭 넘침·단축키 도움말 표시는 이미 구현돼 있어 중복 개발하지 않습니다. [기존 컴포넌트로 다른 앱 정책 연결](component-boundary.md).

## 시작 시점 기록 — 2026-10-27

TVR-5 기준 `b67a4cb`와 TVR-7 초기 구현을 비교한 기록입니다.

| 영역 | Go 시작 시점 | Rust 시작 시점 | 이번 결과와 남은 경계 |
| --- | --- | --- | --- |
| 트리 | `Styler.Tree`: stock tview 노드 색상·역할 적용. 계층·입력은 tview/앱 책임 | 공통 트리 없음 | 양쪽에 안정 ID·펼침·선택·스크롤 모델, 렌더러·조작·예제 추가. [Tree API](tree.md) |
| 탭 | `Styler.Tab(button, active)` 색상만 제공. 탭 목록·닫기·넘침은 앱 책임 | 없음 | 활성/포커스 ID 분리·넘침·변경/닫기 표식·요청 이벤트·공개 렌더러 구현. [API](workspace.md) |
| 패널·분할선 | `Box`, `RefreshBorders`, `Surface` 스타일. 배치·크기 조절은 tview/앱 책임 | `Styles::block(title, focused)` 테두리. 배치는 호스트 책임 | 제목·여백·포커스·ASCII 패널, 열/행 분할·최소 크기·드래그·키보드 조절·좁은 화면 복원 구현 |
| 상태 표시줄 | `FooterButton` 스타일만 제공. 우선순위·생략은 앱 책임 | 예제의 Paragraph, 공개 상태 컴포넌트 없음 | 의미 역할·비색상 표식·상태/단축키 우선순위·항목 단위 생략·생략 개수 구현 |
| 경로 | 전용 API 없음 | 전용 API 없음 | 안정 ID·현재 위치 우선·루트/중간 경로 생략·셀 폭·클릭 이동 요청 구현 |
| 의미별 스타일 | 실제 LazyOra 추출 스타일 + 별도 후보 JSON 해석 | 후보 JSON 코어·Ratatui 변환 | Tree는 같은 후보 JSON 역할로 통일. 기존 Go 스타일 전체와 동등하다는 뜻은 아님 |
| 단말·검증 | tcell 모의 화면·기존 한영 PTY·Go 독립 모듈 검사 | TestBackend·기존 한영 PTY·Cargo 외부 사용 검사 | 전체 공통 컴포넌트의 독립 import·동일 명세·12팔레트·한영 PTY와 통합 입력 검사에 포함 |

## 참고 UI에서 채택한 원칙

[yelog/lazydb](https://github.com/yelog/lazydb)의 고정 커밋 `9c54a65ba35fc594f4ff6f0e7767958563929e7e`를 읽었습니다. 코드를 복사하거나 해당 앱의 DB 타입·상태를 가져오지 않았습니다.

- [Explorer 모델](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/model/explorer.rs): 안정 ID, 펼침 집합, 선택, 논리 행과 뷰포트 구분을 참고했습니다. Tuivory는 DB 카탈로그 대신 앱이 제공하는 평면 부모 ID 목록을 받습니다.
- [Explorer·탭 렌더링](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/ui/mod.rs): 계층 들여쓰기·펼침 표시·아이콘·주/보조 텍스트의 위계와 클릭 영역 구분을 참고했습니다. Tree와 탭의 상태·표식·넘침/클릭 경계에 적용했습니다.
- [배치](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/ui/layout.rs): 최소 크기와 사용자가 선택한 패널 크기를 분리하는 방향을 참고했습니다. 구체적인 앱 전용 너비는 채택하지 않습니다.
- [단축키 힌트](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/ui/shortcut_hints.rs): 셀 폭 측정, 완전한 힌트 단위 배치와 생략 개수 표시를 상태 표시줄의 우선순위·항목 단위 생략에 적용했습니다.

## 단계별 구현 결과

1. **Tree — 로컬 구현 완료**: 공통 데이터·상태·이벤트 명세와 Go/tview·Rust/Ratatui 공개 렌더러, DB 없는 한영 예제, 공통 테스트 데이터·외부 사용 검사.
2. **탭**: 활성/포커스 ID를 분리하고 키보드 탐색 후 확정, 클릭 즉시 활성화, 닫기 요청과 앱 승인, 긴 제목·넘침 처리. 닫기를 요청해도 라이브러리가 앱 문서를 삭제하지 않습니다.
3. **패널·분할선**: 명시적 제목·여백·포커스와 최소 크기, 키보드 크기 조절 및 드래그, 좁은 화면 대체 배치. 크기 선호와 실제 배치를 분리합니다.
4. **상태 표시줄·경로**: 현재 위치를 유지하는 경로 생략, 중요 상태 우선 배치, 상황별 단축키와 메시지의 우선순위·생략 개수. 모든 단계에 같은 의미 역할·비색상 표식·Unicode/ASCII 원칙을 적용합니다.

1~4단계 모두 Go/Rust 공개 API·DB 없는 한영 예제·관련 문서·로컬 검증을 제공했습니다. [통합 사용법](workspace.md)과 [예제](../examples/README.md)를 참고하세요. Tree는 로컬 커밋 2005164, 후속 구현도 사용자 승인에 따라 로컬 커밋으로 저장합니다. 원격 CI·게시 근거는 TVR 일감에 기록하며 실제 원격 단말·LazyOra/LazyBeaver 적용은 별도 검증 대상입니다. TVR-7 에픽은 열린 상태로 유지합니다.

## 2026-10-28 후속 확장

[TVR-8~13 백로그](components-backlog.md)를 기존 TVR-7 에픽 아래 등록했습니다. 첫 단계의 [상태·포커스·팝업 기반](focus.md)은 0.2.0에 포함한 API이며 이전 0.1.0과 변경 범위를 구분합니다. 입력·폼·목록/검색·가상 표·알림·배치/부가 API는 TVR-9~13 후속 구현에 포함합니다. 앱의 완성 Dialog/업무 흐름은 호스트 조합입니다.

## TVR-9~13 결과

공개 Go/Rust [폼](forms.md), [목록·메뉴·검색](collections.md), [가상 그리드](grid.md), [알림·진행·데이터 상태](feedback.md), [간격·배치·Badge/Chip·도움말](layout.md)을 한영 카탈로그·검사와 구현했습니다. 정렬/필터/편집/복사·검증·시간·업무 실행은 앱 책임입니다. Accordion/Drawer/Stepper는 기존 상태·패널을 조합합니다. 단계별 dev 통합을 마쳤으며 0.2.0 릴리스에 포함합니다.

## TVR-17 그리드 구성 (0.3.0)

기존 Grid에 [공통 옵션·프리셋](grid.md)을 추가합니다. Go/Rust 범위 선택·원문 복사·행 번호·열 표시·밀도·상태줄·지연 응답 보호와 같은 데이터 비교 예제를 제공합니다. [로컬 검증](grid-validation.md)과 GitHub CI·태그·실제 LazyOra 적용은 구분합니다.

## TVR-7 공통 메뉴 (0.3.0)

[Menu API](menus.md)의 Go/Rust 계층·메뉴 바·뒤로가기·구분선/비활성/단축키·팝업 배치·원래 문맥 요청을 구현했습니다. 범위 점검에서 확인한 부족분을 사용자의 후속 지시로 보완하며, 앱의 화면/업무 소유권은 바꾸지 않습니다. [검증 기록](../evidence/menu.md).
