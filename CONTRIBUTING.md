# 기여 방법

**한국어 (기본)** · [English](CONTRIBUTING.en.md)

[공통 명세](design/README.md)와 [의존성 경계](docs/architecture.md)를 먼저 확인합니다. 언어 독립 JSON에 프레임워크 타입을 넣지 않고, 언어별 코드에서 토큰 값을 따로 복제하지 않습니다.

문서·테마·도구 변경은 문제와 재현 조건을 먼저 설명하고, 관련 원칙과 검증 방법을 함께 제안해 주세요.

- 규칙: 문제 → 적용 대상 → 규칙 → 예외 → 검증 방법 → 출처.
- 테마: 역할별 전경/배경, 단말 프로필, 속성, 참조 팔레트와 실제 확인 범위.
- 패턴: 기본/포커스/선택/비활성/변경/오류의 상태 조합과 키보드/마우스 계약.
- 어댑터: 앱 데이터·DB·입력 I/O 소유권을 공통 스타일 계산에 넣지 않기.

견본 TUI는 Go 1.24 이상이 필요합니다. Go 변경 시 `make -C go test`와 `make -C go check`, `python3 tools/check_go_module.py`를 실행합니다. Go 소스·모듈 설정은 go/ 안에 두고 공통 디자인 원본은 design/에서 관리합니다. 기본 로컬 빌드는 `make build`로 Linux ARM64 하나를 `bin/go/tuivory-linux-arm64`에 생성합니다. 견본 실행파일은 `bin/<언어>/` 아래에 OS·아키텍처가 포함된 이름으로 둡니다.

Rust 변경 시 Rust 1.85 이상에서 `make test-rust check-rust`, `make check-rust-consumers`, `python3 tools/check_rust_module.py`를 실행합니다. 선택적 Ratatui 어댑터·예제 변경은 Rust 1.88 이상에서 `make test-rust-ui check-rust-ui`, `python3 tools/check_rust_module.py --ratatui` 및 한·영 PTY 검사도 실행합니다. [Rust 견본 문서](docs/rust-playground.md)와 이미지를 함께 갱신합니다. Cargo.toml·Rust 소스는 rust/에 둡니다. 토큰 사본은 생성 도구로 갱신하며 프레임워크 타입·단말 I/O를 코어에 넣지 않습니다. [현재 Rust 범위](rust/README.md)를 확인합니다.

필수 가이드 로컬 검사:

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_palette.py design/themes/lazyora-candidate.csv
python3 tools/check_links.py
python3 tools/export_tokens.py --check
sh -n shell/examples/terminal-colors.sh
```

공통 데이터 변경 시 `make check-consumers`로 Go·Python·Node.js 데이터 해석 결과를 비교합니다. Node.js 18 이상이 필요하며 Python·Node.js 예제에는 외부 의존성이 없습니다. 이 검사는 현재 호스트에서 실행할 Go 검증 프로그램을 임시 디렉터리에 생성하고 종료 후 삭제합니다. 제품 바이너리는 `make build`로 Linux ARM64 하나만 만듭니다.

현재 링크 검사는 로컬 파일의 존재만 검사합니다. 외부 URL과 Markdown 조각 식별자의 유효성은 별도 확인합니다. 실제 단말 결과는 [기록 양식](evidence/README.md)을 사용하며 미확인 환경을 통과로 기록하지 마세요.

앞으로 문서를 새로 작성하거나 수정할 때는 한국어와 영어를 같은 작업에서 함께 반영합니다. 한국어를 기본으로 유지하고 영어판은 `.en.md` 파일로 제공합니다. 기존 한국어 문서만 있는 경우에도 해당 문서를 수정하는 작업에서 영어판을 함께 추가합니다. 두 언어 문서 상단에 서로의 링크를 유지하고 설치 명령·공개 API·지원 범위·검증 결과를 동일하게 반영합니다. UI 이미지는 각 문서의 언어에 맞춰 제공합니다. 아직 번역하지 않은 기존 상세 문서로 연결할 때는 한국어 문서임을 표시합니다. 코드 이름과 공개 형식은 의미를 전달하는 영어 이름을 사용합니다. 커밋 메시지 설명은 한국어로 작성합니다.

기능 추가·수정·버그 수정 시 영향받는 README·사용법·API·예제·UI 이미지·변경 이력 등 관련 문서를 같은 작업에서 현행화합니다. 한국어와 영어를 함께 갱신하고 구현·문서·검증 결과가 일치하는지 확인한 뒤 작업을 완료합니다.

이 프로젝트의 문서·코드는 [AGPL-3.0-only](LICENSE)로 제공합니다. 외부 자료는 출처와 고지 사항을 보존하고 사용 조건을 확인한 뒤 추가하세요.

## 공통 Tree 변경

`design/tree-navigation.json`이 동작 계약의 원본입니다. 수정 후 `python3 tools/export_tree_cases.py`로 Go/Rust 테스트 사본을 함께 갱신하고 양쪽 테스트·외부 import·한영 PTY를 실행합니다. `make check`는 사본 일치도 확인합니다. [점검표](docs/component-audit.md)와 [Tree API](docs/tree.md)를 현행화합니다.

공통 워크스페이스의 계약 원본은 `design/components-cases.json`입니다. 같은 생성 도구로 두 모듈의 사본을 갱신하고 [워크스페이스 안내](docs/workspace.md)의 외부 import·한영 PTY·통합 입력 검사와 이미지를 함께 확인합니다.

## 정적 배포 조건

새 언어·기능·의존성을 추가할 때 배포 실행파일과 적용 앱의 정적 링크 조건을 유지합니다. 빌드 의존성과 실행 시 필요한 외부 런타임을 구분하고 Linux 산출물의 ELF 검사와 대상 커널 실행을 검증합니다. 현재 Python·JavaScript·Shell은 인터프리터 기반 참조 소스입니다. [빌드·외부 앱·CentOS 검증 명령](docs/static-build.md)을 따릅니다.
