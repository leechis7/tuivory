# Tuivory 작업 관리

Tuivory는 LazyOra와 독립된 프로젝트입니다. Jira 표시 이름은 **Tuivory**, 키는 **TVR**입니다.

| 일감 | 범위 | 상태 |
| --- | --- | --- |
| [TVR-1](https://leechis7.atlassian.net/browse/TVR-1) | 기존 구현 기반과 검증 근거 요약 이관 | 완료. 이전본 로컬 재검증과 출처 보존 확인 |
| [TVR-2](https://leechis7.atlassian.net/browse/TVR-2) | 독립 저장소 이전 및 0.0.1 첫 배포 | 완료. [CI 통과](https://github.com/leechis7/tuivory/actions/runs/40057059473) · [0.0.1 배포](https://github.com/leechis7/tuivory/releases/tag/go/v0.0.1) · 공식 Go 프록시를 통한 외부 소비 통과 |
| [TVR-3](https://leechis7.atlassian.net/browse/TVR-3) | 한국어 기본 문서 유지 및 공개용 영어 문서 보강 | 완료. 영어 문서 4종·상호 링크·동기화 원칙 추가. 로컬 문서 검사·Go 예제 컴파일 통과. 커밋·GitHub 게시·원격 CI 미실행 |
| [TVR-4](https://leechis7.atlassian.net/browse/TVR-4) | 견본 UI 다국어 지원 및 영문 문서 이미지 추가 | 완료. `--lang ko\|en`·영문 이미지 4종 추가. 로컬 race/vet·문서 검사·Linux ARM64 빌드 및 양 언어 PTY 시작·종료·화면 복원 통과. 커밋·GitHub 게시·원격 CI 미실행 |

이전 TUIS 일감을 통째로 복사하지 않습니다. 과거 배포·중간 경로 수정 이력은 원본에 보존하며 [이전 요약](migration.md)에서 필요한 출처만 연결합니다. 미구현 언어별 UI 패키지와 실제 단말 검증은 [로드맵](roadmap.md)으로 관리합니다.

칸반 상태는 할 일 → 진행 중 → 검토 → 완료입니다. 작업은 한 번에 하나씩 진행하며 로컬 검증·원격 CI·배포 완료를 구분합니다. 이번 이전 브랜치는 `codex/TVR-2-initial-release`, 통합 브랜치는 main/dev입니다.

GitHub 자동 개발 활동 연동은 GitHub for Atlassian의 저장소 접근 설정에 따릅니다. 브랜치·커밋에 실제 TVR 일감 키를 넣고 수동 출처 링크와 자동 연동 상태를 구분합니다.
