# TVR-9~13 컴포넌트 검증

**한국어 (기본)** · [English](components.en.md)

이 문서는 로컬 구현·검증 방법과 경계를 기록합니다. 단계별 원격 PR/최종 dev CI·병합 커밋은 Jira TVR-9~13 댓글에서 확인하며 이전 단계의 성공을 후속 변경의 결과로 간주하지 않습니다. 승인 범위는 dev 통합이며 main·태그·Release는 별도입니다.

| 단계 | 공개 API와 의미 있는 검증 |
| --- | --- |
| TVR-9 | Form/뷰: grapheme 삭제·커서·읽기 전용·필수/호스트 오류·선택 임시/확정/취소·폭·실제 입력/제출/취소 |
| TVR-10 | List/Menu/SearchPicker: 안정 ID·비활성/구분선 제외·포커스/선택/실행 분리·검색/빈 결과·취소·한글 셀 |
| TVR-11 | GridSource/Grid/뷰: 10만 행에서 뷰포트에 비례한 Row 접근 수·ID 복구·원본 복사·편집 보호·빈 표·열 범위·헤더 정렬 |
| TVR-12 | Notice/Progress/DataState: 중요/액션 알림 유지·큐 포화·요청 불변성·호스트 시각·진행률/취소·높이 1 우선순위 |
| TVR-13 | Spacing/Stack/Badge/Chip/Help: 공유 JSON·0~240셀 비겹침/경계·좁은 화면/선호 복원·0/99+·읽기 전용 제거·키 충돌/우선순위 |

Go race/vet, Rust 전체 기능·rustdoc·fmt·clippy, 공통 토큰/명세·문서 링크·Shell 검사를 사용합니다. 기본 코어 CI는 Rust 1.85.1, UI는 1.88.0입니다. 외부 검사는 go/만 복제하거나 독립 Cargo 패키지를 설치해 공개 API·렌더링과 정적 x86_64 호스트를 확인합니다.

```sh
make test check test-rust-ui check-rust-ui
python3 tools/check_go_module.py --static-output /tmp/go-host
python3 tools/check_rust_module.py --ratatui --static-output /tmp/rust-host
python3 tools/smoke_catalog.py BINARY --mode forms --lang ko
python3 tools/smoke_catalog.py BINARY --mode collections --lang en --ascii
python3 tools/smoke_catalog.py BINARY --mode grid --lang en
python3 tools/smoke_catalog.py BINARY --mode feedback --lang ko
python3 tools/smoke_catalog.py BINARY --mode layout --lang en
```

PTY 검사는 실제 키/마우스 입력·잘못된 조작 방지·40×16 및 120×36 리사이즈·정상 종료/화면 복원을 확인합니다. F2/F3 테마/프로필 전환은 모델을 재생성하지 않습니다. 테스트 도구는 UTF-8 wide 셀·커서 이동을 읽으며 실제 단말·폰트의 시각적 동일성을 보증하지 않습니다.

정적 CI는 Go CGO 비활성화·Rust musl 산출물과 독립 외부 앱의 ELF를 검사하고 공식 CentOS 7.4.1708 사용자 공간/glibc 2.17과 실제 3.10.0-693 커널 VM에서 견본/카탈로그 시작·종료와 외부 API/렌더링을 실행합니다. 카탈로그 VM 시작 검사는 기본 forms 모드이며, 다른 모드는 네이티브 PTY 및 외부 코어 API 검사로 구분합니다.

각 모드의 다크/라이트/흑백 한영 참조는 실제 Rust TestBackend 120×36 SVG 6장, 다섯 모드 총 30장입니다. `tools/snapshot_catalog.py BINARY --mode MODE`로 재현합니다. Go 캡처나 실제 서버/SSH 증거가 아닙니다. [각 사용법](../docs/components-backlog.md)에서 공개 범위와 앱 책임을 확인합니다. DB·실제 클립보드·앱 검증/저장/검색/취소·LazyOra/LazyBeaver 통합은 포함하지 않습니다.
