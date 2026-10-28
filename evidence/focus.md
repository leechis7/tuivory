# TVR-8 상태·포커스·팝업 검증

**한국어 (기본)** · [English](focus.en.md)

2026-10-28, `codex/TVR-8-focus-popup-foundation`의 로컬 변경을 검증했습니다. 이 문서는 게시 전 로컬 검증 근거입니다. 사용자 승인 후 원격 CI·PR·병합 결과는 TVR-8 댓글에 별도로 기록하며 기존 커밋의 CI 성공과 구분합니다. [API·재현 명령](../docs/focus.md)

| 항목 | 결과 |
| --- | --- |
| 같은 계약 | `design/interaction-cases.json`의 6개 상태 합성·24개 연속 시나리오를 Go/Rust에서 검사. 이동·비활성/숨김 제외·중첩·빈 창·입력 라우팅·닫기 요청·복귀·잘못된 요청의 상태 보존 통과 |
| 추가 경계 | 안정 ID 재정렬·순환, 데이터 사본 보존(Go), 최대 64개 팝업·초과 거부, 빈 ID·필수 역할 검사 통과 |
| 테마·표현 | 3테마×4색상 프로필의 역할·포커스 스타일 검사, 상태 표식 유지 통과 |
| Go | race 테스트·vet 및 독립 go/ 외부 import·렌더링 검사 통과 |
| Rust 코어 | Rust 1.85.1 기본 기능 테스트·rustdoc·fmt·clippy 통과 |
| Rust UI | Rust 1.88.0 전체 기능 테스트·rustdoc·fmt·clippy, 패키징 crate 외부 Ratatui API·렌더링 검사 통과 |
| 실제 PTY | Go·Rust 각각 한국어/영어에서 Tab/Shift+Tab·비활성 건너뛰기·busy 실행 차단·중첩 팝업·배경 클릭 차단·Esc 복귀·테마/프로필/ASCII 전환·40×16 및 120×36 리사이즈·Ctrl+Q 종료/화면 복원 통과 |
| 정적 배포 | Go CGO 비활성화·Rust musl x86_64 예제와 외부 앱의 ELF 아키텍처/로더/공유 라이브러리 검사 통과 |
| CentOS 7.4 | 실제 `3.10.0-693.el7.x86_64` 커널·7.4.1708 사용자 공간·glibc 2.17 VM에서 새 Go/Rust 예제 한영 시작·종료/복원 4개, 외부 정적 앱 API/렌더링 통과 |
| 한영 이미지 | 실제 Rust TestBackend 120×32의 다크·라이트·흑백·팝업·중첩·ASCII 각 언어 6장, 총 12장 생성·언어 검사 통과 |
| 공통 자산·문서 | 토큰·컴포넌트 계약 동기화, 팔레트·로컬 문서 링크·Shell 구문 검사 통과 |

CentOS 재현은 `tools/check_centos74.py`에 새 두 예제를 `--binary`로, 외부 앱을 `--consumer`로 전달합니다. 로그는 `/tmp/tuivory-focus-centos74.log`, 원본 해시는 `/tmp/tuivory-focus-centos74.json`, 보존 해시는 [JSON 기록](focus-results.json)입니다. 커널·이미지 다이제스트는 검사기에 고정되어 있습니다. QEMU TCG의 실제 구형 게스트 커널 검증이며 최신 호스트 커널을 공유하는 컨테이너 실행만으로 판정하지 않았습니다.

입력 편집·폼 제출·완성 Dialog 위젯, 실제 대상 서버·SSH·폰트·LazyOra/LazyBeaver 통합은 이번 결과에 포함하지 않습니다. 모의 화면·참조 SVG·로컬 PTY·구형 커널 VM을 구분하며 코어가 단말이나 DB를 소유한다는 뜻이 아닙니다. 기본 제품 빌드는 늘리지 않았고 실제 공개 전 단계별 승인을 받습니다.
