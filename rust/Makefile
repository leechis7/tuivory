.PHONY: test check tokens test-ui check-ui run build build-x86_64
CARGO_TARGET_DIR ?= target
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
	cargo run --locked --features playground --example playground -- $(ARGS)
build:
	CARGO_TARGET_DIR="$(CARGO_TARGET_DIR)" python3 ../tools/build_rust.py --arch arm64
build-x86_64:
	CARGO_TARGET_DIR="$(CARGO_TARGET_DIR)" python3 ../tools/build_rust.py --arch x86_64
