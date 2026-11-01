.PHONY: run build test check
run:
	go run ./cmd/tuivory $(ARGS)
build:
	python3 ../tools/build_examples.py go
test:
	go test -race ./...
check:
	go vet ./...
