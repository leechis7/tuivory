# Tuivory 0.2.0 릴리스

**한국어 (기본)** · [English](release-0.2.0.en.md)

제품 `VERSION`과 Rust manifest/lock의 버전은 **0.2.0**입니다. [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.2.0)에서 정적 실행파일·독립 crate·체크섬을 제공합니다. Go·Rust 태그는 같은 최종 커밋을 가리킵니다. TVR-5/6/7 에픽은 열린 상태로 유지합니다.

## 포함할 변경

| 범위 | 내용 |
| --- | --- |
| Go·Rust 정적 배포 | Go CGO 비활성화, Rust musl/번들 LLD, ELF 로더·공유 라이브러리 거부, CentOS 7.4 x86_64 실행·외부 정적 앱 검증 |
| [TVR-8 상태·포커스](focus.md) | 공통 상태 합성, 안정 ID, 중첩 팝업 스코프, 닫기 요청·포커스 복귀 |
| [TVR-9 입력·폼](forms.md) | grapheme 편집·읽기 전용·필수/호스트 오류, 체크·라디오·선택·제출 요청 |
| [TVR-10 목록·검색](collections.md) | ID 기반 목록·메뉴, 비활성/구분선, 포커스/선택/실행 분리, 검색·확정/취소 |
| [TVR-11 데이터 그리드](grid.md) | 가상 데이터 소스, 셀/행 선택, 뷰포트, 편집·복사·정렬·필터 요청 |
| [TVR-12 피드백](feedback.md) | 알림 큐·중요 오류 보존, 진행·취소 요청, 로딩/빈 결과/실패 상태 |
| [TVR-13 배치](layout.md) | 간격·밀도·Stack/Drawer 배치, Badge/Chip, 우선순위 키보드 도움말 |
| [TVR-14 Go 그리기](overlay-drawing.md) | 카드·그림자 좌우의 두 칸 문자 보정, Show 이후 출력 회귀 |

TVR-8~13은 양 언어 모델·공개 어댑터·DB 없는 한영 예제를 포함합니다. 카탈로그는 5모드, 한영 dark/light/blackwhite 참조는 30장입니다. TVR-14는 Go/tcell 수정이며 Rust 동일 API 추가로 간주하지 않습니다. 기존 Tree·탭·패널·분할·경로 API도 유지합니다.

호스트가 데이터·DB·검증·저장·검색·클립보드 I/O·시계·단말 수명주기를 소유합니다. Python·JavaScript·Shell은 계속 인터프리터 기반 토큰 참조 예제이며 UI 라이브러리나 독립 실행파일 배포가 아닙니다. 실제 LazyOra/LazyBeaver·고객 서버 SSH 통합 검증은 포함하지 않습니다.

## 설치와 태그

```sh
go get github.com/leechis7/tuivory/go@v0.2.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.2.0", features = ["ratatui"] }
```

Go에는 모듈 자신의 버전을 기록하는 go.mod 필드가 없으며 `go/v0.2.0` 태그가 모듈 버전을 결정합니다. Rust는 `publish = false`를 유지하며 crates.io에 게시하지 않습니다. 로컬 개발 시 Go replace/Rust path 의존성도 사용할 수 있습니다. 기존 0.1.0에는 TVR-8~14의 새 API가 없습니다.

Go 1.24 이상, Rust 코어 1.85 이상(1.85.1 검증), Ratatui/카탈로그 1.88 이상(1.88.0 검증)입니다. Go의 기존 추출 스타일과 공통 후보 토큰은 서로 다른 데이터입니다.

## 배포 산출물

Release 첨부와 로컬 `bin/releases/v0.2.0/`의 파일명은 아래와 같습니다. 각 Linux 아카이브는 해당 언어의 정적 playground와 5모드 catalog, 한영 실행 안내·출처·라이선스를 포함합니다. 기본 `make build`는 그대로 Go Linux ARM64 하나만 생성합니다. 카탈로그·x86_64·Rust는 명시적 준비 명령으로 생성합니다.

| 파일 | 용도 |
| --- | --- |
| `tuivory-go-v0.2.0-linux-arm64.tar.gz` | Go Linux ARM64 견본·카탈로그 |
| `tuivory-go-v0.2.0-linux-x86_64.tar.gz` | Go CentOS 7.4 대상 x86_64 견본·카탈로그 |
| `tuivory-rust-v0.2.0-linux-arm64.tar.gz` | Rust Linux ARM64 musl 견본·카탈로그 |
| `tuivory-rust-v0.2.0-linux-x86_64.tar.gz` | Rust CentOS 7.4 대상 x86_64 musl 견본·카탈로그 |
| `tuivory-0.2.0.crate` | 독립 Rust 소스·공개 API·예제·내장 데이터 |
| `SHA256SUMS` | 아카이브·crate 체크섬 |

자산은 확정 커밋에서 정적 빌드하고 검사합니다. `RELEASE-MANIFEST.json`은 빌드 커밋·버전·아카이브/바이너리 해시·최종 검증을 기록하는 첨부 자산입니다. 기존 0.1.0 태그와 자산은 교체하지 않습니다. 과거 Rust GNU ARM64 자산의 glibc 2.39 의존성과 새 musl 정적 자산을 구분합니다.

## 검증과 게시 기록

[준비 검증 기록](../evidence/release-0.2.0.md)은 게시 전 dirty 후보를 검사한 과거 기록입니다. 최종 배포 자산의 SHA256은 Release 첨부 `SHA256SUMS`·`RELEASE-MANIFEST.json`을 기준으로 확인하세요. PR/main/dev CI·확정 커밋·실제 태그 설치·업로드 자산 재다운로드 검증 결과는 [TVR-7](https://leechis7.atlassian.net/browse/TVR-7)과 TVR-5/6 댓글에 기록합니다. 이전 준비 후보의 해시나 CI를 최종 자산의 근거로 사용하지 않습니다.

검증 범위는 정적 ELF·외부 Go/Rust import·한영 native PTY와 CentOS 7.4 커널 실행입니다. VM catalog 시작은 기본 forms 모드이며 다른 모드의 입력은 native PTY로 확인합니다. 실제 고객 서버 SSH·폰트별 물리 단말·LazyOra/LazyBeaver 앱 통합은 별도입니다.
