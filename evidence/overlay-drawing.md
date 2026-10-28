# TVR-14 오버레이 경계 검증

**한국어 (기본)** · [English](overlay-drawing.en.md)

2026-10-28, Linux ARM64의 Go/tcell v2.13.10에서 검사했습니다. [TVR-14](https://leechis7.atlassian.net/browse/TVR-14) · [API·재현 범위](../docs/overlay-drawing.md).

## 재현과 수정

수정 전 최소 재현에서 `(2,0)`에 `한`, `(3,0)`에 테두리 `│`를 기록하고 `Show()`를 호출하면 `(3,0)`의 논리 값은 `│`지만 `GetContents()` 출력은 비어 있었습니다. 또 `Z` 위에 `界`를 그린 뒤 시작 칸만 덮으면 숨겨졌던 `Z`가 출력에 다시 나타났습니다.

`WideSafeScreen`은 겹치는 기존 grapheme의 전체 셀과 새 잔여 칸을 정리합니다. `DimRegion`은 사각형 양쪽 경계의 잘린 grapheme을 지우고 내부 문자를 유지합니다. `PanelView`, 공개 Choice와 Go 견본의 팝업·선택박스가 같은 내부 구현을 사용합니다.

## 통과한 로컬 검사

| 방법 | 결과 |
| --- | --- |
| `make test check` | Go 전체 race·vet, 토큰/계약 사본·팔레트·링크·도구·Shell 검사 통과 |
| `go/drawing_test.go` | 다섯 쓰기 경로·한글/CJK/이모지·카드/그림자 좌우·다중 프레임·Sync·끝 열·잘림·스타일을 Show 이후 Runes/Bytes로 검사 |
| 실제 위젯 통합 | Go 팝업의 포커스 테두리·열린 Choice 목록·Unicode/ASCII 패널을 Show 이후 검사 |
| `tools/check_go_module.py --static-output /tmp/tuivory-tvr14-external-x86_64` | 저장소 design/ 없는 독립 모듈·외부 단일 import 앱의 새 API 출력 검사, x86_64 ELF의 PT_INTERP/DT_NEEDED 부재 검사 통과 |
| Go PTY | playground 한영 시작/종료·화면 복원, focus 한영 중첩/마우스 차단/상태/테마/ASCII/리사이즈, catalog 5모드 한글 입력/테마/리사이즈/복원 통과 |

새 검사는 기존 CI의 Go 전체 테스트·외부 import 경로에 포함됩니다. 이 문서는 커밋·게시 전 로컬 검증 시점의 기록입니다. 후속 커밋·PR·원격 CI·dev 병합 결과는 TVR-14 댓글에 기록합니다. 정적 실행파일의 CentOS VM 재실행·실제 고객 서버/SSH·글꼴별 단말·LazyOra 앱 통합은 이번 로컬 검사에 포함되지 않습니다. Rust/Ratatui는 이번 수정 대상이 아닙니다. 기존 릴리스·태그는 변경하지 않았습니다.
