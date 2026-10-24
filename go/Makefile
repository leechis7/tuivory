.PHONY: run build test check
run:
	go run ./cmd/tuivory
build:
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -o ../bin/tuivory-linux-arm64 ./cmd/tuivory
test:
	go test -race ./...
check:
	go vet ./...
