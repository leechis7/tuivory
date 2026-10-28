.PHONY: run build test check check-consumers test-rust check-rust check-rust-consumers test-rust-ui check-rust-ui run-rust build-rust
run:
	$(MAKE) -C go run
build:
	$(MAKE) -C go build
test:
	$(MAKE) -C go test
	python3 -m unittest discover -s tests -v
check:
	$(MAKE) -C go check
	python3 tools/export_tokens.py --check
	python3 tools/export_tree_cases.py --check
	python3 tools/check_palette.py design/themes/lazyora-candidate.csv
	python3 tools/check_links.py
	sh -n shell/examples/terminal-colors.sh
check-consumers:
	python3 tools/check_consumers.py
test-rust:
	$(MAKE) -C rust test
check-rust:
	$(MAKE) -C rust check
	python3 tools/export_tokens.py --check
check-rust-consumers:
	python3 tools/check_consumers.py --rust
test-rust-ui:
	$(MAKE) -C rust test-ui
check-rust-ui:
	$(MAKE) -C rust check-ui
run-rust:
	$(MAKE) -C rust run ARGS="$(ARGS)"
build-rust:
	$(MAKE) -C rust build

.PHONY: build-go-x86_64 build-rust-x86_64
build-go-x86_64:
	$(MAKE) -C go build-x86_64
build-rust-x86_64:
	$(MAKE) -C rust build-x86_64

.PHONY: run-focus-go run-focus-rust
run-focus-go:
	go -C go run ./examples/focus $(ARGS)
run-focus-rust:
	cargo run --manifest-path rust/Cargo.toml --locked --features playground --example focus -- $(ARGS)

.PHONY: run-tree-go run-tree-rust
run-tree-go:
	go -C go run ./examples/tree $(ARGS)
run-tree-rust:
	cargo run --manifest-path rust/Cargo.toml --locked --features playground --example tree -- $(ARGS)

.PHONY: run-workspace-go run-workspace-rust
run-workspace-go:
	go -C go run ./examples/workspace $(ARGS)
run-workspace-rust:
	cargo run --manifest-path rust/Cargo.toml --locked --features playground --example workspace -- $(ARGS)

.PHONY: run-catalog-go run-catalog-rust
run-catalog-go:
	go -C go run ./examples/catalog $(ARGS)
run-catalog-rust:
	cargo run --manifest-path rust/Cargo.toml --locked --features playground --example catalog -- $(ARGS)
