# Tuivory 문서

**한국어 (기본)** · [English](README.en.md)

문서는 현재 저장소 구현을 기준으로 유지합니다. 현재 Go 버전은 `v0.1.0`이며 Rust도 Git 태그 `rust/v0.1.0`으로 배포합니다. 신규 작성·수정과 기능 변경 시 관련 한국어·영어 문서를 함께 갱신합니다.

| 문서 | 내용 |
| --- | --- |
| [프로젝트 소개](../README.md) | 제공 범위·설치·빠른 시작 |
| [설치·사용 안내](installation.md) | 현재 모듈·CLI·토큰 식별자와 배포/소스 구분 |
| [Rust 패키지](../rust/README.md) | Git 배포 crate·공통 토큰·스타일·Ratatui 어댑터·외부 사용 |
| [Rust 견본](rust-playground.md) | Ratatui 어댑터·한영 실행·조작·이미지·검증 |
| [공통 UI 점검](component-audit.md) · [Tree API](tree.md) | Go·Rust 지원/앱 책임·후속 계획·공통 Tree·검증 |
| [공통 워크스페이스](workspace.md) | 탭·패널·분할·상태 표시줄·경로 API·통합 예제·검증 |
| [Go 사용법](go-package.md) | 공개 API·역할·상태·테마 재적용 |
| [견본](playground.md) | 한국어·영어 실행·키 조작·이미지 생성 |
| [저장소 구조](architecture.md) | 언어별 경계·공통 데이터·내장 자산 |
| [공통 명세](../design/README.md) | 언어 독립 설계 계약 |
| [토큰](../design/tokens/README.md) · [테마](../design/themes/README.md) | JSON·스키마·CSV와 검증 범위 |
| [설계 원칙](principles.md) | 의미·프로필·상태·입력·셀·검증 |
| [컴포넌트 패턴](patterns.md) | 위젯별 상태와 조작 계약 |
| [단말 프로필](terminal-profiles.md) | 색상 능력·ANSI·표현 제한 |
| [추출 출처](lazyora-extraction.md) · [Go 범위](go-style-coverage.md) | 원본 해시·API 대응·동등성 근거 |
| [언어별 예제](../examples/README.md) | Go·Rust·Python·JavaScript·Shell의 실제 제공 범위 |
| [로드맵](roadmap.md) | 구현 상태와 후속 범위 |
| [작업 관리](work-tracking.md) | TVR·PR·CI·게시 상태 |
| [검증 양식](../evidence/README.md) · [초기 배포 근거](../evidence/initial-migration.md) | 계산·시뮬레이션·실제 단말 및 배포 기록 |
| [공식 참고 자료](sources.md) · [출처 고지](../NOTICE.md) | 설계 참고와 저작권·라이선스 |
| [기여 안내](../CONTRIBUTING.md) · [작업 규칙](../AGENTS.md) | 문서 현행화·검증·승인 원칙 |
| [변경 이력](../CHANGELOG.md) | 태그 배포와 미배포 변경 |

현재 제품명은 Tuivory, 공개 Go 패키지는 `tuivory`, 일감 프로젝트는 TVR입니다. 이전 원출처 이름은 라이선스·출처 고지에서만 식별합니다. [LICENSE](../LICENSE)는 원문을 유지합니다.
