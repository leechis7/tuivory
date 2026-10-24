# 기여 방법

[공통 명세](design/README.md)와 [의존성 경계](docs/architecture.md)를 먼저 확인합니다. 언어 독립 JSON에 프레임워크 타입을 넣지 않고, 언어별 코드에서 토큰 값을 따로 복제하지 않습니다.

문서·테마·도구 변경은 문제와 재현 조건을 먼저 설명하고, 관련 원칙과 검증 방법을 함께 제안해 주세요.

- 규칙: 문제 → 적용 대상 → 규칙 → 예외 → 검증 방법 → 출처.
- 테마: 역할별 전경/배경, 단말 프로필, 속성, 참조 팔레트와 실제 확인 범위.
- 패턴: 기본/포커스/선택/비활성/변경/오류의 상태 조합과 키보드/마우스 계약.
- 어댑터: 앱 데이터·DB·입력 I/O 소유권을 공통 스타일 계산에 넣지 않기.

견본 TUI는 Go 1.24 이상이 필요합니다. Go 변경 시 `make -C go test`와 `make -C go check`, `python3 tools/check_go_module.py`를 실행합니다. Go 소스·모듈 설정은 go/ 안에 두고 공통 디자인 원본은 design/에서 관리합니다. 기본 로컬 빌드는 `make build`로 Linux ARM64 하나만 생성합니다.

필수 가이드 로컬 검사:

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_palette.py design/themes/lazyora-candidate.csv
python3 tools/check_links.py
python3 tools/export_tokens.py --check
sh -n shell/examples/terminal-colors.sh
```

공통 데이터 변경 시 `make check-consumers`로 Go·Python·Node.js 소비 결과를 비교합니다. Node.js 18 이상이 필요하며 Python·Node.js 예제에는 외부 의존성이 없습니다. 이 검사는 현재 호스트에서 실행할 Go 검증 프로그램을 임시 디렉터리에 생성하고 종료 후 삭제합니다. 제품 바이너리는 `make build`로 Linux ARM64 하나만 만듭니다.

현재 링크 검사는 로컬 파일의 존재만 검사합니다. 외부 URL과 Markdown 조각 식별자의 유효성은 별도 확인합니다. 실제 단말 결과는 [기록 양식](evidence/README.md)을 사용하며 미확인 환경을 통과로 기록하지 마세요.

문서는 우선 한국어로 작성하고 README에는 영어 요약을 유지합니다. 코드 이름과 공개 형식은 의미를 전달하는 영어 이름을 사용합니다. 커밋 메시지 설명은 한국어로 작성합니다.

이 프로젝트의 문서·코드는 [AGPL-3.0-only](LICENSE)로 제공합니다. 외부 자료는 출처와 고지 사항을 보존하고 사용 조건을 확인한 뒤 추가하세요.
