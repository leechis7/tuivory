# Tuivory 작업 관리

**한국어 (기본)** · [English](work-tracking.en.md)

Tuivory는 독립 프로젝트이며 Jira 표시 이름은 **Tuivory**, 키는 **TVR**입니다. 기능·문서 작업은 실제 TVR 일감을 확인한 뒤 진행합니다.

| 일감 | 범위 | 검증·게시 상태 |
| --- | --- | --- |
| [TVR-1](https://leechis7.atlassian.net/browse/TVR-1) | 기반과 검증 근거 | 완료. 초기 구현과 출처 보존 검증 |
| [TVR-2](https://leechis7.atlassian.net/browse/TVR-2) | 독립 저장소 및 첫 Go 배포 | 완료. [CI](https://github.com/leechis7/tuivory/actions/runs/40057059473) · [go/v0.0.1 Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.0.1) · Go 프록시를 통한 외부 프로젝트 사용 검증 통과 |
| [TVR-3](https://leechis7.atlassian.net/browse/TVR-3) | 한·영 문서와 동기화 원칙 | 최초 문서 보강은 [PR #1](https://github.com/leechis7/tuivory/pull/1)로 병합·게시. 후속 전체 현행화는 한·영 29쌍 정리와 로컬 검증 완료. 후속 게시·CI 결과는 TVR-3 댓글에 기록 |
| [TVR-4](https://leechis7.atlassian.net/browse/TVR-4) | 견본 언어 선택과 영문 이미지 | 완료. 한국어·영어 UI, 영문 이미지 4종, 양 언어 PTY 검사. PR #1 병합·게시 |
| [TVR-5](https://leechis7.atlassian.net/browse/TVR-5) | Rust 생태계 에픽 | 진행 중. Rust 코어·Ratatui 어댑터·한영 대화형 견본·독립 패키지·문서·이미지 로컬 구현 및 검증. Rust Git 태그 rust/v0.1.0 배포. 실제 LazyBeaver 적용은 별도 검증하며 CI·게시 근거는 일감 댓글 참조 |
| [TVR-6](https://leechis7.atlassian.net/browse/TVR-6) | Go 모듈 에픽 | 진행 중 유지. Go go/v0.1.0 배포에 언어별 bin 경로와 공통 API 포함. CI·게시 근거는 일감 댓글 참조 |
| [TVR-7](https://leechis7.atlassian.net/browse/TVR-7) | Go·Rust 공통 UI 에픽 | 진행 중. 지원 점검·Tree·탭·패널·분할·상태·경로 양 언어 구현 및 로컬 검증·커밋. v0.1.0 배포. CI·게시 근거는 댓글 참조, 실제 앱 적용은 별도 검증 |

PR #1의 병합 커밋은 `5c3242ff17c719d7558d447c93477234f75fe698`입니다. [dev CI](https://github.com/leechis7/tuivory/actions/runs/40062239810)와 [main CI](https://github.com/leechis7/tuivory/actions/runs/40062241916)는 모두 통과했습니다. 이 병합은 새 태그·Release 배포가 아니며 당시 배포된 Go 버전은 `v0.0.1`이었습니다. 현재 버전은 `v0.1.0`입니다.

통합 브랜치는 `main`·`dev`, 작업 브랜치는 `codex/실제-TVR-키-설명`을 사용합니다. 상태는 할 일 → 진행 중 → 검토 → 완료이며 한 번에 하나의 작업을 진행합니다. 기능 변경 시 관련 문서도 한국어·영어 함께 현행화하고 로컬 검증·원격 CI·게시·태그 배포를 구분합니다. 커밋·GitHub 게시는 해당 변경에 대한 명시적 승인이 필요합니다.

후속 작업의 로컬 검증 결과는 해당 TVR 일감 댓글에 기록합니다. 기존 PR의 성공 CI를 후속 로컬 변경의 CI 결과로 간주하지 않습니다.

GitHub 자동 개발 활동 연동은 GitHub for Atlassian의 저장소 접근 설정에 따릅니다. 수동 출처 링크와 자동 연동 완료를 구분합니다. 미구현 언어별 UI 패키지와 실제 단말 검증은 [로드맵](roadmap.md)을 참고하세요.

## 정적 배포 후속 작업

TVR-5·TVR-6에서 Go·Rust와 후속 언어의 정적 배포·호스트 정적 링크 조건을 반영했습니다. CentOS 7.4 x86_64 실제 게스트 커널·외부 앱·한영 견본과 ARM64 로컬 검사를 통과했습니다. [검증 기록](../evidence/static-build.md). 사용자 승인으로 소스 게시를 진행합니다. 원격 CI·PR·병합 결과는 TVR-5·TVR-6 댓글에 기록하며 기존 v0.1.0 태그·자산은 유지합니다. 에픽은 열린 상태를 유지합니다.

## 공통 컴포넌트 확장 백로그

사용자 승인으로 TVR-7 아래 TVR-8~13을 추천 순서로 등록했습니다. [순서·범위·게시 기준](components-backlog.md). TVR-8의 로컬 구현·검증을 마쳤으며 사용자 승인으로 소스 게시를 진행합니다. 원격 CI·PR·병합 근거는 TVR-8 댓글에 기록합니다. TVR-9~13은 백로그에 두고 에픽은 열린 상태를 유지합니다. 원격 CI·게시를 로컬 검증과 구분합니다.
