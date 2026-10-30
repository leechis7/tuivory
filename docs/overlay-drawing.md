# 두 칸 문자와 오버레이 그리기 — TVR-14

**한국어 (기본)** · [English](overlay-drawing.en.md)

Go/tcell의 팝업·카드·드롭다운·그림자 경계를 한글·CJK·이모지가 가로지르면 논리 버퍼의 테두리가 `Show()` 출력에서 누락되거나, 가려졌던 이전 문자가 다시 나타날 수 있습니다. 문자열 자르기만으로는 아래에 있던 두 칸 문자의 시작·잔여 칸을 정리하지 못합니다.

`WideSafeScreen`과 `DimRegion`은 이 경계를 보정하는 Go 0.2.0 공개 API입니다. 이번 수정은 Go/tcell 경로이며 Rust/Ratatui API나 검증 완료를 뜻하지 않습니다. 필수 네이티브 라이브러리·런타임 의존성을 추가하지 않습니다.

## 앱에서 사용

```go
// screen은 앱이 초기화하고 소유하는 tcell.Screen입니다.
// 매 프레임 배경 → 그림자 → 카드 순으로 그립니다.
background.Draw(screen)
tuivory.DimRegion(screen, tuivory.CellRect{
    X: cardX + 1, Y: cardY + 1, Width: cardWidth, Height: cardHeight,
})
card.SetRect(cardX, cardY, cardWidth, cardHeight)
card.Draw(tuivory.WideSafeScreen(screen))
screen.Show() // tview Application이 출력한다면 앱에서 중복 호출하지 않습니다.
```

카드 테두리와 내부를 그리는 **전체 Draw 호출**에 래퍼를 전달합니다. 한 칸씩 직접 그리는 코드에도 같은 화면을 사용합니다. `SetContent`, `SetCell`, `Put`, `PutStr`, `PutStrStyled`가 모두 같은 보정을 거칩니다. `Put`은 첫 grapheme과 나머지 문자열을 구분하고 결합 문자·ZWJ 이모지 등을 보존합니다. 화면 마지막 열에 들어가지 못하는 두 칸 문자는 한 칸 공백으로 바꾸며, 반환 폭은 실제 저장한 한 칸입니다. 영역 밖 쓰기는 무시합니다. 카드 내부의 너비 제한·문자열 생략은 여전히 위젯/호스트가 담당합니다.

쓰기 영역과 겹친 기존 두 칸 문자는 양쪽 칸을 공백으로 지웁니다. 따라서 왼쪽 시작 칸이나 오른쪽 잔여 칸이 카드 밖에 있으면 그 한 칸도 지워지며, 바깥쪽의 원래 스타일은 유지합니다. 새 두 칸 문자의 잔여 칸도 정규화해 나중에 이전 문자가 되살아나지 않게 합니다. 온전히 보이는 이웃 문자는 유지합니다.

`DimRegion(screen, rect)`는 화면 안으로 잘린 사각형에 Dim 속성을 적용합니다. 영역 안에 완전히 들어간 grapheme은 유지하고, 양쪽 경계에 걸린 두 칸 문자는 전체를 공백으로 바꿉니다. 바깥 칸의 스타일은 바꾸지 않습니다. 카드와 그림자의 경계는 별개이므로 그림자를 그리고 나서 카드를 안전 화면으로 그립니다. 그림자가 두 개의 띠로 구성되면 각 사각형에 호출할 수 있습니다.

`PanelView`, 공개 `Choice`의 열린 목록, Go 견본의 팝업·선택박스는 이미 공통 보정을 사용합니다. 외부 tview 위젯으로 만든 카드는 위처럼 직접 감싸야 합니다. 중복 래핑은 같은 화면을 반환합니다. 래퍼는 단말 초기화·입력·`Show`/`Sync`를 원래 화면으로 전달하고 별도의 이벤트 루프를 만들지 않습니다.

팝업 닫기·이동·리사이즈 시에는 **앱 데이터로 배경을 다시 그립니다**. API는 배경 스냅샷을 저장하거나 잘린 글자를 자동 복구하지 않습니다. tview처럼 UI 그리기 고루틴에서 호출하며, 여러 셀 보정을 동시 쓰기 트랜잭션으로 제공하지 않습니다.

## 검증

`go/drawing_test.go`는 `SimulationScreen.Show()` 후 **`GetContents()`의 출력 Runes와 Bytes**를 검사합니다. `GetContent()`만 확인하면 출력에서 빠지는 테두리를 발견하지 못합니다. 다음 검사가 포함됩니다.

- 한글·CJK·단일/ZWJ/국기 이모지와 다섯 쓰기 API의 좌우 경계, 잔여 문자, 무관한 이웃 보존.
- 배경 재그리기·팝업 재열기·다중 프레임·`Sync`, 겹친 두 칸 문자 교체, 결합 문자와 화면 끝.
- 그림자 양쪽 경계, 내부 grapheme, 바깥 스타일 보존, 음수·화면 밖·극단 좌표의 잘림.
- dark/light/blackwhite × 8/16/256/truecolor의 그림자, Unicode/ASCII 패널 테두리.
- 실제 Go 견본의 포커스된 팝업 테두리와 열린 `Choice` 목록을 `Show()` 후 검사.

```sh
make test check
python3 tools/check_go_module.py
```

외부 단일 import 검사도 두 API를 호출하고 `Show()` 출력 버퍼를 검사합니다. 이 결과는 tcell 시뮬레이션이며 고객 서버·SSH·폰트별 실제 단말 검증을 대신하지 않습니다. 커밋·원격 CI·게시 여부는 TVR-14 기록에서 구분합니다.

[Go API](go-package.md) · [팝업·포커스](focus.md) · [견본](playground.md)

0.5.0 TVR-19는 기본 끄기의 공통 팝업 그림자를 제공합니다. `off/auto/solid/dim`, 카드와 그림자를 포함한 위치 계산, 그림자를 제외한 입력 판정과 두 칸 문자 경계 보호를 지원합니다. 앱이 배경 다시 그리기와 열기·닫기를 결정합니다. [API·실행 예제·12팔레트 화면](popup-shadows.md).
