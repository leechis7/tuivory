# TUIS에서 Tuivory로 이전

Tuivory는 TUI + ivory에서 이름을 가져온 터미널 UI 스타일 패키지 프로젝트입니다. 첫 버전은 0.0.1입니다.

기존 [TUIS 저장소](https://github.com/leechis7/tuis)의 Go 스타일·견본·공통 자료와 미게시 언어 중립 구조 전환 작업을 이관했습니다. 기존 저장소의 Git 이력·태그·Release는 보존하며, 새 저장소에는 과거 배포 버전이나 중간 경로 변경 이력을 재현하지 않습니다.

## Go 앱 전환

```sh
go get github.com/leechis7/tuivory/go@v0.0.1
```

```go
import "github.com/leechis7/tuivory/go"

styler, err := tuivory.New("dark", "256")
```

기존 `tuis.New` 같은 호출의 패키지 이름을 `tuivory`로 바꾸세요. 공개 API와 스타일 계산을 유지합니다. 앱의 go.mod에서 이전 의존성 제거는 호스트 저장소에서 `go mod tidy`로 확인합니다. LazyOra 작업 트리는 이 이전 작업에서 수정하지 않습니다.

공통 토큰의 초안 식별자는 `tuivory.tokens.draft`로 바뀝니다. 토큰 파일을 직접 읽는 소비자는 형식 검사도 함께 변경해야 합니다. CLI는 `tuivory`, 견본 이미지 생성 환경변수는 `TUIVORY_SNAPSHOT_DIR`입니다.

## 보존한 구현과 출처

- 테마 3개 × 색상 프로필 4개, 원본 240개 색상 값과 1,572개 스타일 사례.
- 상태를 보존하는 stock tview 적용, 그리드·구문 스타일 함수, DB 없는 견본.
- 언어 중립 토큰·스키마·CSV, Python/JavaScript 소비 예제, Shell 참조 출력.
- [TUIS-2](https://leechis7.atlassian.net/browse/TUIS-2): 견본 구현.
- [TUIS-4](https://leechis7.atlassian.net/browse/TUIS-4): 공통 자료와 실제 스타일 추출.
- [TUIS-6](https://leechis7.atlassian.net/browse/TUIS-6): 언어 중립 구조와 Go 하위 모듈.

LazyOra 원본 파일과 커밋 해시는 [추출 기록](lazyora-extraction.md)에 남아 있습니다. AGPL-3.0-only와 저작권 고지는 유지합니다. [NOTICE](../NOTICE.md)
