# LazyOra 스타일의 첫 Go 패키지 추출

**한국어 (기본)** · [English](lazyora-extraction.en.md)

Tuivory는 여러 언어에서 사용할 터미널 UI 스타일 패키지를 제공하며, 첫 구현은 LazyOra에서 실제 다듬은 Go/tcell/tview 스타일을 추출합니다. 앱이나 DB 코드를 함께 옮기지 않습니다.

## 원본과 보존 범위

원본 기준 커밋: [4530a1156853fa8629a16f654f87680fe2b52e01](https://github.com/leechis7/lazyora/commit/4530a1156853fa8629a16f654f87680fe2b52e01). 로컬 작업 트리에 다른 문서 변경이 있었지만 아래 Go 파일에는 미커밋 변경이 없었습니다.

| 원본 | 추출 내용 | 파일 SHA-256 |
| --- | --- | --- |
| [theme.go](https://github.com/leechis7/lazyora/blob/4530a1156853fa8629a16f654f87680fe2b52e01/internal/ui/theme.go) | 실제 테마 팔레트, 입력·선택·버튼·편집기 스타일, 배경별 경계색, 폼·모달 처리 | `9acafb3ef7c245d3256ebcb8c06d1a447ed6168d9efe3cd55ef3bbd30b2f42ce` |
| [style_tokens.go](https://github.com/leechis7/lazyora/blob/4530a1156853fa8629a16f654f87680fe2b52e01/internal/ui/style_tokens.go) | 테마/색상 프로필 해석, 선택·변경·비활성·포커스 토큰 | `014314dfe40e64ac5bf35e8740579b3b661717be04d2e73b6db24242c54ee4d4` |
| [widgets.go](https://github.com/leechis7/lazyora/blob/4530a1156853fa8629a16f654f87680fe2b52e01/internal/ui/widgets.go) | 목록·체크박스 스타일 | `113550fd413a8e3e40c1134c369e99172a73854d767fc12477c03a1278d1fd08` |

현재 `tuivory.NewStyles(theme, profile)`는 원본의 색상값과 계산 순서를 유지합니다. `screen`, 사용자 설정, 단말 I/O 대신 명시적 인자를 받으며 모든 색상은 반환 값에 포함됩니다. 입력·선택·변경됨 스타일은 각각 독립된 메서드입니다.

`go/internal/widgets`는 입력·버튼·편집기·목록·체크박스·폼·모달·단순 표에 스타일을 적용합니다. 값을 지우거나 위젯을 다시 만들지 않습니다. `Form`은 tview가 매 Draw에서 색상을 덮는 문제를 처리하기 위해 입력과 읽기 전용 설명의 DrawFunc를 소유합니다. 앱에서 이미 훅을 쓰면 개별 스타일 함수를 사용하거나 훅을 합성해야 합니다.

포커스 순환·모달 배경 입력 차단·앱 전체 위젯 탐색은 호스트 앱의 책임입니다. 후속 보완에서 그리드 팔레트·상태 합성과 구문 역할별 스타일 계산도 추출했습니다. SQL lexer·DB 연결·앱 상태·로컬 tview 포크는 포함하지 않습니다. stock tview에서 동작합니다.

## CSV 후보와 실제 구현의 차이

[candidate.json](../design/tokens/candidate.json)은 설계 단계 CSV에서 생성한 교차 언어 참조 예제입니다. 실제 LazyOra 팔레트와 같다고 주장하지 않습니다. 예를 들어 실제 dark/truecolor 편집기 배경은 `#242d3a`, 버튼 배경은 `#81a1c1`입니다.

Go 견본은 실제 추출 패키지의 팔레트와 입력·버튼·드롭다운·그리드 스타일을 사용합니다. 기존 16개 견본 역할로 대응시키며 원본에 별도 색이 없는 success/error는 본문색과 상태 문구로 나타냅니다. 공통 JSON 예제는 기존 후보를 유지합니다. 실제 구현을 공통 데이터로 옮길 때는 이 차이를 명시적으로 해소합니다.

## 사용 템플릿

```sh
go -C go run ./examples/starter
go -C go run ./cmd/tuivory --lang en
```

starter는 폼·입력·체크박스·버튼과 F2 테마 전환을 제공하며 DB가 없고 라벨은 한국어입니다. 견본 언어 선택은 현재 소스 기능으로 배포된 `v0.0.1` 태그에는 포함되지 않습니다. 결정적인 견본을 위해 색상 프로필은 256으로 지정합니다. 호스트가 화면을 소유하면 `ProfileForColors(screen.Colors(), limited)`로 감지 결과를 전달할 수 있습니다.

## 검증

[원본 출력 fixture](../go/internal/style/testdata/lazyora-styles.json)는 원본 팔레트와 토큰 함수만 독립 실행해 기록한 12프로필 × 20색상 값입니다. Tuivory resolver의 출력으로 fixture를 생성하지 않았습니다. 테스트는 이 240개 값을 비교합니다.

다시 캡처할 때에는 위 커밋의 로컬 체크아웃 경로를 명시합니다. 이 명령은 fixture를 갱신하므로 원본 변경과 함께 검토합니다.

```sh
python3 tools/capture_lazyora_styles.py /path/to/lazyora
make -C go test
make -C go check
```

기존 견본의 12프로필·3화면 대비·테마 왕복·선택·모달 검사를 유지합니다. 추가 폼 검사는 읽기 전용 설명의 실제 렌더링 색상과 값·포커스 보존을 확인합니다. 실제 단말 검증과 GitHub CI·게시 여부는 별도로 기록합니다.

## Go 패키지 완전성 보완

[스타일 범위표](go-style-coverage.md)는 추출한 계산과 검증 범위를 정리합니다. [사용법](go-package.md)은 역할·상태·테마 재적용 API를 설명합니다. 원본 240색상 비교 외에 전경·배경·속성의 1,572개 원본 스타일 사례를 추가했습니다.

```sh
python3 tools/capture_lazyora_matrix.py /path/to/lazyora
```

구문 스타일 계산은 stock tcell에서 사용할 수 있습니다. stock tview의 TextArea에는 LazyOra 포크의 `SetTextStyleFunc`가 없으므로 Tuivory는 그 훅을 복제하지 않습니다. 실제 LazyOra import 전환 시 기존 호스트 lexer와 훅에서 Tuivory의 `SyntaxStyle`을 호출하는 구조로 연결합니다. 템플릿에서 구문 강조 렌더링까지 제공한다고 표현하지 않습니다.
