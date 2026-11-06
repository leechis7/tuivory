.PHONY: run build test check check-consumers test-rust check-rust check-rust-consumers test-rust-ui check-rust-ui run-rust build-rust
run:
	$(MAKE) -C go run ARGS="$(ARGS)"
build:
	$(MAKE) -C go build
.PHONY: run-syntax-go run-syntax-rust
run-syntax-go:
	go -C go run ./examples/syntax $(ARGS)
run-syntax-rust:
	cargo run --manifest-path rust/Cargo.toml --features playground,syntax-sql --example syntax -- $(ARGS)
.PHONY: build-syntax-go build-syntax-rust
build-syntax-go: build
build-syntax-rust: build-rust
test:
	$(MAKE) -C go test
	python3 -m unittest discover -s tests -v
check:
	$(MAKE) -C go check
	python3 tools/check_ui_facade.py
	python3 tools/export_syntax_words.py --check
	python3 tools/check_api_lifecycle.py
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

.PHONY: run-controls-go run-controls-rust
run-controls-go:
	go -C go run ./examples/controls $(ARGS)
run-controls-rust:
	cargo run --manifest-path rust/Cargo.toml --locked --features playground --example controls -- $(ARGS)

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

.PHONY: run-menu-go run-menu-rust
run-menu-go:
	go -C go run ./examples/menu $(ARGS)
run-menu-rust:
	cargo run --manifest-path rust/Cargo.toml --locked --features playground --example menu -- $(ARGS)

.PHONY: build-c build-cpp build-java test-c test-cpp test-java
build-c:
	python3 tools/build_language.py c
build-cpp:
	python3 tools/build_language.py cpp
build-java:
	python3 tools/build_language.py java
test-c:
	python3 tools/check_languages.py --language c
test-cpp:
	python3 tools/check_languages.py --language cpp
test-java:
	python3 tools/check_languages.py --language java
