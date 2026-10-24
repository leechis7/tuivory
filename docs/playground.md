# Tuivory 견본 사용법

**한국어 (기본)** · [English](playground.en.md)

이 화면에서 ‘규칙을 적용하면 어떻게 보이는가’를 직접 확인합니다. 데이터는 합성 예시이며 DB·네트워크 서비스에 접속하거나 설정/입력값을 저장하지 않습니다.

## 실행

```sh
go -C go run ./cmd/tuivory
```

이 문서는 현재 저장소 소스 기준입니다. `--lang`은 배포된 `v0.0.1` 이후 추가되어 아직 새 태그로 배포하지 않았습니다. Go 1.24 이상이 필요합니다. mise 사용자는 `mise install` 후 평소처럼 `go`를 실행하면 됩니다. 기본 로컬 바이너리:

```sh
make build
./bin/tuivory-linux-arm64
```

`make build`는 Linux ARM64만 만듭니다. 다른 환경에서는 `go -C go run ./cmd/tuivory`로 현재 환경에서 실행할 수 있습니다.

```sh
go -C go run ./cmd/tuivory --theme light --colors 16
go -C go run ./cmd/tuivory --theme blackwhite --colors 8 --mouse=false
go -C go run ./cmd/tuivory --lang en
```

`--theme`: dark / light / blackwhite. `--colors`: auto / 8 / 16 / 256 / truecolor.

`--lang`: ko / en. 한국어가 기본이며, 동일한 바이너리에서 영어를 선택할 수 있습니다. 예: `./bin/tuivory-linux-arm64 --lang en`. 별도 영어 전용 빌드는 필요하지 않습니다.

색상 선택은 **토큰 프로필 미리보기**이며 실제 터미널 능력이나 팔레트를 변경하지 않습니다. 표현할 수 없는 색상은 라이브러리/단말이 근사할 수 있습니다. 자동 모드는 라이브러리가 보고하는 능력을 사용합니다. TERM이 없으면 이 프로세스에서만 ansi를 사용합니다.

## 조작

| 키 | 동작 |
| --- | --- |
| Tab / Shift+Tab | 현재 화면의 조작 대상을 순서대로 이동 |
| 방향키 | 목록·그리드·선택박스 탐색, 버튼 그룹 좌우 이동 |
| Enter | 버튼 실행·선택박스 펼침·그리드 이름 셀 편집 |
| F1 | 스크롤 가능한 도움말 팝업 |
| F2 | 다크 → 라이트 → 흑백 순환 |
| F3 | 자동 → 8 → 16 → 256 → True Color 순환 |
| F4 | 현재 입력값 미리보기 팝업 |
| F5 | 입력 오류 표시 켜기/끄기 |
| F6 | 컴포넌트 → 색상 토큰 → 조작 안내 전환 |
| Esc | 열린 선택박스 또는 팝업부터 닫기 |
| Ctrl+Q | 종료 |

마우스로도 선택·버튼·체크박스·그리드를 조작할 수 있습니다. 모달 바깥 클릭은 뒤 화면을 실행하거나 팝업을 닫지 않습니다. 모달 내부에서 Tab이 순환하고 닫으면 호출 지점으로 포커스가 돌아갑니다.

## 먼저 해볼 것

1. 이름을 바꾸고 체크박스와 선택값을 변경합니다.
2. F2/F3을 눌러 보면서 값과 선택이 유지되는지 확인합니다.
3. 그리드의 이름 셀에서 Enter → 새 값 입력 → Tab → 저장을 실행합니다. `* 변경됨` 표시를 확인합니다.
4. F4로 팝업을 열고 F2로 테마를 바꾼 뒤 Esc로 돌아옵니다.
5. F6의 색상 토큰 화면에서 16개 역할의 실제 전경/배경 견본을 비교합니다.

일반 화면은 80×24 이상이 필요합니다. 100열 미만에서는 왼쪽 메뉴를 숨겨 견본 공간을 확보하며 F6로 모든 화면에 접근합니다. 더 작으면 창을 넓히라는 안내를 표시하고 크기를 복구하면 기존 팝업·입력 상태로 돌아옵니다.

## 화면과 검증 범위

[다크](images/playground-dark.svg) · [라이트](images/playground-light.svg) · [흑백](images/playground-blackwhite.svg) · [팝업](images/playground-popup.svg)

영어 UI: [다크](images/playground-dark-en.svg) · [라이트](images/playground-light-en.svg) · [흑백](images/playground-blackwhite-en.svg) · [팝업](images/playground-popup-en.svg)

이미지는 실제 앱 위젯을 tcell 모의 화면에 그린 뒤 셀에서 생성한 참조 이미지입니다. 실제 SecureCRT/MobaXterm 캡처나 지원 보장으로 해석하지 않습니다. 별도 단말 검증은 [양식](../evidence/README.md)을 사용합니다.

```sh
make -C go test
make -C go check
python3 tools/smoke_playground.py bin/tuivory-linux-arm64
python3 tools/smoke_playground.py bin/tuivory-linux-arm64 --lang en
TUIVORY_SNAPSHOT_DIR="$PWD/docs/images" go -C go test ./internal/playground -run '^TestSnapshot$' -count=1
```

위 스냅샷 검사는 한국어·영어 이미지를 함께 생성합니다. 영어 이미지 이름에는 `-en`이 붙습니다.

상태 문구는 실제 카드 배경에서 대비를 다시 확인하고, 색상 강조의 대비가 부족하면 카드의 본문색으로 표시합니다. 상태의 의미는 ‘정상/주의/오류’ 문구로 유지합니다.

견본의 색상은 [LazyOra 실제 스타일에서 추출한 Go 패키지](lazyora-extraction.md)를 사용합니다. 공통 JSON은 역할 표시 순서와 교차 언어 데이터 예제에 사용하며, CSV 후보는 실제 추출 팔레트와 구분합니다. SQL 편집기·DB 기능·범용 위젯 SDK를 포함하지 않습니다.
