# 배경 누출 수정 검증 — TVR-7

**한국어 (기본)** · [English](background-fix.en.md)

이 단계 이후 비활성 전경을 재조정하고 일반 항목의 표식을 제거했습니다. 현재 규칙과 검증은 [비활성 상태 비교](../docs/disabled-states.md)를 참고하세요. 아래 숫자와 JSON 해시는 이전 단계 기록입니다.


[수정 전 조사](../docs/background-audit.md)에서 확인한 문제를 같은 미커밋 브랜치에서 보완합니다. 원본 토큰·raw 스타일 API·그리드 옵션은 바꾸지 않습니다. [한영 디자인 가이드](../design/surfaces.md).

## 수정

- Go/Rust 공통 Rows와 경로/상태 Line의 body/hint/disabled/info/success/warning/error 평문은 실제 surface 배경으로 그립니다. 대비가 부족하면 더 나은 표면 전경을 사용합니다.
- field/button/selection/edited/header/editor/grid.* 및 사용자 역할은 그대로 유지합니다. 일반 Badge/Chip은 평문 규칙을 사용합니다. 탭 구간·목록 선택 너비·simple/data 그리드 디자인은 바꾸지 않습니다.
- Go NewGridView는 PreserveBackgrounds를 사용하며 Rust GridWidget도 같은 원래 역할 보존 경로를 사용합니다. 수동 행 조합에는 Go RowsView.PreserveBackgrounds / Rust RowsWidget.preserve_backgrounds()를 제공합니다.
- Go TextOnSurface/ControlStyleOnSurface와 Rust Styles::text_on_surface/control_on_surface를 외부 앱에 제공합니다. 기존 raw API는 유지합니다.
- 기존 Go 직접 DropDown/Choice의 바탕/라벨, Apply의 지정 표면, Go/Rust focus 및 Rust menu/tree/workspace/playground 텍스트 문맥을 보완합니다. Go 견본의 기존 전경 보정도 같은 공통 함수로 통일합니다.

## 검증 범위

수정 전과 같은 Go 564회·Rust 384회, 총 948개 셀 렌더링을 대조합니다. 그리드 행은 공개 GridView/GridWidget과 같은 명시적 배경 보존 경로로 검사합니다. 평문 대상에서는 글자/행 끝의 배경 차이를 제거하고, 그리드·탭·트리·메뉴의 의도한 배경 관찰값은 이전과 일치하는지 확인합니다. 실제 글자가 있는 평문 850개 구간의 참조 대비도 검사하며 최소값은 약 4.504:1입니다.

12팔레트에서 Go Show 이후 물리 출력과 Rust TestBackend의 라벨/스팬·경로/상태·선택/수정·사용자 역할·raw 보존·명시적 canvas 및 light-16 success 전경 보정 회귀를 추가합니다. Go 전체 race/vet와 독립 모듈 소비 예제, Rust 전체 기능/대상·doctest/fmt/Clippy 및 독립 crate 적용 앱을 검사합니다. 실제 PTY는 모델/선택/입력·테마 변경·리사이즈·종료가 유지되는지 확인합니다.

최종 실행 결과·소스/이미지 해시·미실행 항목은 [결과 JSON](background-fix-results.json)을 기준으로 확인합니다. UI 참조는 한국어·영어를 함께 갱신하며 Go SimulationScreen / Rust TestBackend 결과입니다. 실제 서버·SSH·폰트별 물리 단말과 구분합니다.

## 재현

```sh
go -C go test -race ./...
go -C go vet ./...
make test-rust-ui check-rust-ui
python3 tools/check_go_module.py
python3 tools/check_rust_module.py --ratatui
python3 tools/smoke_playground.py bin/go/tuivory-linux-arm64 --lang ko --resize
python3 tools/check_links.py
python3 tools/export_tokens.py --check
```

조사용 전수 probe·원시 로그는 Git 제외 bin/validation/background-audit/와 background-fix/에 보관합니다. 수정 전 JSON은 과거 결과로 보존합니다. 이 작업은 미커밋·미게시 소스이며 원격 CI·CentOS 검증·태그·Release는 실행하지 않습니다.

## 이전 비활성 표시 시안 (후속 수정으로 대체)

Help·목록/검색·폼·알림의 비활성 액션에 `[-]`, 메뉴 바에 기존 메뉴와 같은 `-` 표식을 추가합니다. 비활성 입력값과 버튼은 활성 배경 대신 disabled 역할을 사용하며 기존 값·실행 제외 규칙은 유지합니다. 양쪽 언어에서 표식·값 보존·메뉴 바 너비/클릭 제외 회귀를 검사하고, 영향받는 카탈로그·메뉴 20개 PTY를 추가로 실행합니다. 한영 가이드와 참조 화면도 함께 갱신합니다.
