.PHONY: test check tokens test-ui check-ui run build
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
	cargo build --locked --release --target aarch64-unknown-linux-gnu --target-dir "$(CARGO_TARGET_DIR)" --features playground --example playground
	mkdir -p ../bin/rust
	cp "$(CARGO_TARGET_DIR)/aarch64-unknown-linux-gnu/release/examples/playground" ../bin/rust/tuivory-linux-arm64
