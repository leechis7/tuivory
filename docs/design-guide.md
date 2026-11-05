# 디자인 가이드

**한국어 (기본)** · [English](design-guide.en.md)

언어별 구현이 함께 따르는 표시·조작 규칙입니다. 테마와 단말 표현 능력은 앱이 선택합니다.

- [설계 원칙](principles.md)
- [컴포넌트 패턴](patterns.md)
- [표면·대비](../design/surfaces.md)
- [비활성 상태](disabled-states.md)
- [단말 프로필](terminal-profiles.md)
- [토큰](../design/tokens/README.md)
- [테마](../design/themes/README.md)

## 0.11.0 그리드 상태 규칙

[그리드 데이터 작업](grid-workspace.md)은 편집/승인 대기/오류 표면, 항상 남는 변경 셀 `*`와 독립 행 표식을 정의합니다. 선택·포커스로 변경 여부를 지우지 않습니다. 행의 Edited는 다른 셀을 변경색으로 칠하지 않습니다. 고정/일반 열 영역은 겹치지 않고 좁은 단말에서 자르며 표시/순서/보기 상태는 안정 ID를 사용합니다. 권한·NULL 값·승인/트랜잭션·전체 검색·파일 저장은 호스트 책임입니다. 모든 테마/색상 수와 Unicode/ASCII는 기존 의미 역할을 사용합니다. [공통 컨트롤 규칙](../design/controls.md).
