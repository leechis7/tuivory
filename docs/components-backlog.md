# 공통 컴포넌트 확장 백로그

**한국어 (기본)** · [English](components-backlog.en.md)

2026-10-28 MUI 비교 검토를 바탕으로 사용자 승인 후 TVR-7 에픽 아래 등록했습니다. 기존 Tree·탭·패널·분할·상태·경로는 재사용하고, Go의 스타일 지원·견본 내부 구현과 Go/Rust 공통 공개 컴포넌트를 구분합니다.

| 순서 | 일감 | 범위 | 상태 |
| --- | --- | --- | --- |
| 1 | [TVR-8](https://leechis7.atlassian.net/browse/TVR-8) | 공통 상태·포커스·팝업 기반 | dev 구현·검증 완료. PR/CI·병합 근거는 Jira 댓글 참조 |
| 2 | [TVR-9](https://leechis7.atlassian.net/browse/TVR-9) | 입력·버튼·체크·라디오·선택·폼 | dev 구현·검증 완료. PR/CI·병합 근거는 Jira 댓글 참조 |
| 3 | [TVR-10](https://leechis7.atlassian.net/browse/TVR-10) | 목록·메뉴·검색 선택 | dev 구현·검증 완료. PR/CI·병합 근거는 Jira 댓글 참조 |
| 4 | [TVR-11](https://leechis7.atlassian.net/browse/TVR-11) | 표·데이터 그리드 | dev 구현·검증 완료. PR/CI·병합 근거는 Jira 댓글 참조 |
| 5 | [TVR-12](https://leechis7.atlassian.net/browse/TVR-12) | 알림·진행·로딩/빈 결과/오류 | dev 구현·검증 완료. PR/CI·병합 근거는 Jira 댓글 참조 |
| 6 | [TVR-13](https://leechis7.atlassian.net/browse/TVR-13) | 배치·밀도 토큰·Badge/Chip·도움말 등 | dev 구현·검증 완료. PR/CI·병합 근거는 Jira 댓글 참조 |

각 단계에서 구현·한영 문서/이미지·검증을 마친 뒤 결과와 커밋·게시 여부를 알리고 해당 단계의 명시적 승인을 받습니다. 이전 단계의 게시 승인을 다음 단계에 적용하지 않습니다. 커밋·게시 전에는 다음 기능 브랜치를 시작하지 않으며 TVR-7 에픽은 열린 상태로 유지합니다.

공통 모델은 상태·이벤트·표현 명세를 제공하고 앱이 검증·검색·DB·업무 실행·시간·외부 I/O·단말 수명주기를 연결합니다. 모든 단계에서 정적 링크, 동일한 Go/Rust 동작, 한영 예제, Unicode/ASCII·색상 프로필·좁은 화면을 검증합니다. 기존 라이브러리가 제공하는 동작은 재사용하고 필요할 때 공통 어댑터·조합을 추가합니다.

참고는 [MUI 컴포넌트](https://mui.com/material-ui/all-components/), [입력](https://mui.com/material-ui/react-text-field/), [Dialog](https://mui.com/material-ui/react-dialog/), [MUI X Data Grid](https://mui.com/x/react-data-grid/), [테마](https://mui.com/material-ui/customization/theming/)입니다. 웹의 픽셀·DOM·그림자·애니메이션은 터미널 셀·포커스·키보드 조작에 맞게 판단합니다. 명령 팔레트는 검색+목록+팝업 조합으로 검토하고 이미지·전용 아이콘 폰트가 필요한 기능은 우선순위를 낮춥니다.

각 단계의 승인된 소스 게시·병합은 `dev`까지만 진행합니다. 전체 작업 완료 후 사용자의 별도 릴리스 지시로 `main` 반영·태그·Release를 진행하며 단계마다 main/dev를 동기화하지 않습니다.

2026-10-28 사용자가 TVR-9~13의 순차 구현·검증·커밋·게시와 단계별 dev 병합을 명시적으로 승인했습니다. 이 다섯 단계는 추가 승인 질문 없이 진행하고 단계별 결과를 알립니다. main·태그·Release는 별도 지시를 기다립니다.

TVR-8~13의 공개 API·예제를 dev 통합 순서로 완료했습니다. 최초 점검/승인 기록과 현재 구현 상태를 구분합니다. main·태그·릴리스, 실제 앱/SSH 적용과 다른 언어는 별도 후속 범위입니다.

## TVR-17 그리드 구성 (0.3.0)

기존 Grid에 [공통 옵션·프리셋](grid.md)을 추가합니다. Go/Rust 범위 선택·원문 복사·행 번호·열 표시·밀도·상태줄·지연 응답 보호와 같은 데이터 비교 예제를 제공합니다. [로컬 검증](grid-validation.md)과 GitHub CI·태그·실제 LazyOra 적용은 구분합니다.

## TVR-7 책임 범위 정정 후속

[책임 범위](component-boundary.md)와 [현재 점검표](component-audit.md)에 따라 기존 TVR-7 에픽에서 문서/예제 정정을 진행합니다. 앱의 화면 조합·전역 포커스/키·업무 연결은 앱 책임입니다. 중첩 메뉴는 미제공 후보로 기록하며 새 일감 등록·구현은 이번 작업에 포함하지 않습니다. 탭 넘침과 단축키 도움말은 이미 제공합니다. 이 정정은 50bf212로 커밋하고 PR #16으로 dev에 통합했습니다. 이후 구현한 메뉴·그리드 옵션과 함께 0.3.0에 포함합니다.

## TVR-7 메뉴 개선

사용자의 후속 지시로 기존 에픽에서 [공통 메뉴](menus.md)를 구현합니다. 앞 절의 후보 기록 이후 단계이며 새 일감 번호를 만들지 않았습니다. 계층·복귀·바·표시/조작은 라이브러리, 메뉴 분류·전역 키·명령 실행은 호스트 책임입니다. 메뉴 소스는 27e6019로 커밋하고 PR #16으로 dev에 통합했으며 0.3.0에 포함합니다.
