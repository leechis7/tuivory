# Tuivory 문서

**한국어 (기본)** · [English](README.en.md)

0.11.0: [그리드 편집·데이터 작업](grid-workspace.md). 0.11.0부터 제공합니다.

**0.10.1 사용 금지:** [업그레이드·회수 안내](withdrawn-versions.md). 0.10.2 이상을 사용하세요.

0.10.0 TVR-7: [Go 반응형 Modal](modals.md)은 좁은 단말 안에서 긴 버튼을 여러 행으로 배치합니다. Modal은 backend를 내장한 SDK 어댑터이며 원시 별칭 정체성의 예외입니다. 0.10.0에 포함합니다.
0.10.0 TVR-18: [Go/Rust 탭·트리 드래그 앤 드롭](drag-drop.md)은 기본 끄기이며 앱 승인 후 불변 모델 적용, 영역 밖 캡처·취소·키보드 대안을 제공합니다. 0.10.0부터 제공합니다.

**0.9.1 TVR-27:** [통합 예제 실행파일](examples.md)은 언어별 하나이며 현재 Linux 서버 아키텍처만 빌드합니다. `--demo tree`, `--demo menu`, `--demo syntax` 등으로 선택합니다.

**0.9.0 TVR-24:** [선택적 Oracle SQL/PLSQL 분석·공통 토큰·편집기 전환](syntax.md)을 제공합니다. Go는 루트 한 번만 import하고 Rust는 syntax-sql 기능으로 선택합니다.

**0.10.0:** Go UI를 `github.com/leechis7/tuivory/go` 하나로 구성합니다. 기존 하위 경로는 호환용으로 유지합니다. [단일 import·이름 대응](ui-facade.md).

현재 릴리스는 **0.11.1**입니다. 설치 → 컴포넌트 사용법 → API 명세 순서로 읽으세요.

- [설치·빠른 시작](installation.md)
- [컴포넌트 가이드](components.md)
- [API 명세](api/README.md)
- [디자인 가이드](design-guide.md)
- [전체 예제](examples.md)
- [앱과 라이브러리의 책임](component-boundary.md)
- [개발·검증·이력](development.md)

[현재 릴리스](release-0.11.1.md)

0.7.0 TVR-26: Go·Rust에서 Tuivory 경로만 사용하는 UI 구성, 공통 입력·바이트 span 변환과 터미널 수명을 제공합니다. [API 대응·예제·현재 제공 상태](ui-facade.md).

[Python·TypeScript/JavaScript·C·C++·Java 독립 지원](languages.md): 미배포 패키지·Tree 검증 작업입니다. 구현과 런타임은 언어별로 독립적이며 기존 공개 0.11.1은 유지합니다.
