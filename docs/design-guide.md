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

## 그리드 실제 커서 (0.11.1)

편집 버퍼에 가짜 커서 문자를 넣지 않습니다. 텍스트·마우스·로컬 커서가 같은 grapheme 뷰포트를 사용합니다. 포커스 뷰는 위치·가시성만 소유하며 NULL·승인 대기·클리핑·무효화·포커스 해제 때 오래된 커서를 숨깁니다. Go는 NewGridView와 NewCursorScreen/PreserveCursorTty로 backend 기본 모양·깜빡임 명령을 제거합니다. Rust는 GridWidget::render_frame을 사용하고 버퍼 전용 Widget은 실제 커서를 등록하지 않습니다. 전역 포커스·레이어 선택은 앱 책임입니다. [연결·근거](grid-workspace.md).

[Python·TypeScript/JavaScript·C·C++·Java 독립 지원](languages.md): 미배포 패키지·Tree 검증 작업입니다. 구현과 런타임은 언어별로 독립적이며 기존 공개 0.11.1은 유지합니다.

[독립 언어 workspace API·예제](language-workspace.md): 탭·패널·분할·경로·상태줄을 다섯 구현에서 검증했습니다. 나머지 카탈로그 이식은 진행 중입니다.
