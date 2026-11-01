.PHONY: test check tokens test-ui check-ui run build
CARGO_TARGET_DIR ?= $(abspath ../.cache/rust)
test:
	cargo test --locked --all-targets
	cargo test --locked --doc
check:
	cargo fmt --all -- --check
	cargo clippy --locked --all-targets -- -D warnings
tokens:
	cargo run --locked --example tokens -- dark 256
test-ui:
	cargo test --locked --all-targets --all-features
	cargo test --locked --doc --all-features
check-ui:
	cargo fmt --all -- --check
	cargo clippy --locked --all-targets --all-features -- -D warnings
run:
	cargo run --locked --features playground,syntax-sql --example showcase -- $(ARGS)
build:
	CARGO_TARGET_DIR="$(CARGO_TARGET_DIR)" python3 ../tools/build_rust.py
