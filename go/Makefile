.PHONY: run build build-x86_64 test check
run:
	go run ./cmd/tuivory
build:
	mkdir -p ../bin/go
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -o ../bin/go/tuivory-linux-arm64 ./cmd/tuivory
	python3 ../tools/check_static_elf.py --arch arm64 ../bin/go/tuivory-linux-arm64
build-x86_64:
	mkdir -p ../bin/go
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -o ../bin/go/tuivory-linux-x86_64 ./cmd/tuivory
	python3 ../tools/check_static_elf.py --arch x86_64 ../bin/go/tuivory-linux-x86_64
test:
	go test -race ./...
check:
	go vet ./...
