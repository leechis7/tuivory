# LazyOra → Tuivory Go 스타일 범위

**한국어 (기본)** · [English](go-style-coverage.en.md)

기준: LazyOra `4530a1156853fa8629a16f654f87680fe2b52e01`. [캡처 manifest](../go/internal/style/testdata/lazyora-source.json)에 원본 파일 SHA-256을 기록합니다. 원본에서 추출한 스타일을 아래 기준으로 검증합니다.

| 원본 스타일 | Tuivory API | 검증 |
| --- | --- | --- |
| `theme.go`, `style_tokens.go`의 실제 팔레트 | `tuivory.NewStyles` | 3테마 × 4프로필 × 20색상 = 240개 값 |
| 표면·의미별 텍스트 | `SurfaceColor`, `SurfaceText`, `TextColor`, `TextStyle` | 모든 표면/텍스트 역할 조합 |
| 입력·선택·버튼·포커스·비활성·변경·편집기 | 각각의 `*Style` 메서드 | 원본 메서드의 전경·배경·속성 |
| 배경에 따른 포커스 경계 | `BorderStyle`, `RefreshBorders` | 5표면 × 포커스 유무 |
| `grid.go` 팔레트·셀·헤더·활성 셀 | `GridColors`, `GridCellStyle`, `GridHeaderStyle`, `GridActiveStyle` | 줄무늬/현재 행/NULL/변경/범위의 모든 조합 |
| 행번호·구분선·그리드 상태줄 | `GridGutterStyle`, `GridDividerColor`, `GridStatusStyle` | 원본의 ANSI·흑백·라이트 분기 |
| `sql_colors.go` 스타일 계산 | `SyntaxStyle` | 5표면 × 7구문 역할. lexer는 호스트 책임 |
| `choice.go` 선택 필드 | `DropDownStyle`, `DropDown`, `NewChoice`/`Choice` | 프로필별 원본 값, 폼 덮어쓰기, 한글 겹침 회귀 |
| `widgets.go`의 목록·체크박스·트리 | `List`, `Checkbox`, `Tree` | 기존 위젯 적용 및 역할별 재색상 |
| `theme.go`의 폼·모달·편집기 | `Form`, `Modal`, `Editor` | 폼 실제 렌더링, 값·내부 포커스 유지 |
| `styleDataTable`, 비교표 | `TableOn`, `ComparisonHeaderStyle` | 본문/헤더 상태, 흑백 헤더 예외 |
| `tabs.go`, `toolbar.go` | `TabStyle`/`Tab`, `FooterButtonStyle`/`FooterButton` | 활성 탭·푸터 전경/배경·속성 |
| `panel_resize.go`, `form_popup.go` | `SplitterStyle`, `PopupBackdrop`, `PopupCardStyle`, `PopupShadowStyle` | 제한 색상 옵션 및 원본 속성 보존 |
| `theme_apply.go` 스타일 순회 | `Apply`, `Roles`, `StyleChildren` | 숨겨진 페이지 재색상, 값·선택·포커스·스크롤 보존 |

표 전체의 기본 색상·계산 스타일은 12프로필의 [1,572개 원본 사례](../go/internal/style/testdata/lazyora-matrix.json)로 대조합니다. 앱 화면별 문자열·키맵·DB 분기·SQL 단어 목록·범위 선택 좌표 계산·팝업 레이아웃/입력 라우팅을 공통 코어로 복제하지 않습니다. 스타일 계산에 필요한 상태만 명시적으로 받습니다.

브라우저/정의 화면의 별도 강조 헤더(`Accent`, Panel 배경, Bold), 상태·안내 문구는 공개 역할과 tcell 스타일 속성을 조합해 표현할 수 있습니다. 앱별 의미를 공통 이름으로 강제하지 않습니다.

캡처 명령은 로컬 LazyOra 체크아웃의 Go 스타일 파일이 HEAD와 같은지 확인한 뒤 원본 함수만 임시 Go 프로그램에서 실행합니다. Oracle·LazyOra 패키지를 import하지 않습니다. 정규 Go 테스트에서는 fixture만 사용하므로 LazyOra 체크아웃이 필요하지 않습니다.

```sh
python3 tools/capture_lazyora_styles.py /path/to/lazyora
python3 tools/capture_lazyora_matrix.py /path/to/lazyora
make -C go test
```

공통 컴포넌트의 신규 Tree API는 [Go·Rust Tree 사용법](tree.md)에서 설명합니다. 기존 Go 추출 스타일·stock `Styler.Tree`와 별도의 후보 팔레트 기반 구현이며 현재 배포 태그에는 포함되지 않습니다. [TVR-7 지원 범위 점검](component-audit.md)에서 상태·조작·앱 책임과 남은 단계를 구분합니다.
