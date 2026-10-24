# Tuivory Go

Go 모듈과 모든 Go 구현은 이 디렉터리에 있습니다. 모듈 경로는 `github.com/leechis7/tuivory/go`, 패키지 이름은 `tuivory`이며 한 번만 import합니다.

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

첫 배포는 `v0.0.1`입니다. 저장소의 `go/` 하위 모듈이므로 태그는 `go/v0.0.1`을 사용합니다.

```sh
go get github.com/leechis7/tuivory/go@v0.0.1
```

저장소 루트에서:

```sh
make run
make build
make test
make check
```

이 디렉터리에서는 `go run ./cmd/tuivory`, `go run ./examples/starter`, `go test -race ./...`를 실행할 수 있습니다. `make build`는 Linux ARM64 제품 바이너리 하나를 저장소의 `bin/`에 만듭니다.

공통 후보 토큰의 원본은 [design/tokens](../design/tokens/README.md)에 있습니다. `internal/tokens/candidate.json`은 `tools/export_tokens.py`로 생성한 배포용 복사본입니다. 수동 수정하지 않습니다. Go 모듈을 단독 다운로드해도 이 파일을 embed하므로 레포 루트 데이터나 별도 생성 단계 없이 사용할 수 있습니다.

[API와 사용법](../docs/go-package.md) · [스타일 범위](../docs/go-style-coverage.md)
