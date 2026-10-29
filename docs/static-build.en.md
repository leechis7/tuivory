# Static distribution and CentOS 7.4

[한국어 (default)](static-build.md) · **English**

Current release: **0.3.0**. [Assets and validation](release-0.3.0.en.md). The 0.2.0/CentOS details below are historical.

Per the user instruction on 2026-10-29, CentOS validation is no longer performed, including the CI VM job. Static distribution requirements, ELF inspection and execution checks in available environments remain. The CentOS commands and previous results below are historical reproduction records, not current required procedures.

Static executables are included in **0.2.0**; existing 0.1.0 assets are preserved. [Assets, installation and validation](release-0.2.0.en.md).

Distributed executables for Go, Rust and future languages without an explicit exception must run without a dynamic loader, shared libraries or a separately installed language runtime. Those packages must not introduce mandatory native dependencies that prevent static host linking. Build-time Go modules and Rust crates are allowed; shared tokens are embedded so runtime data files are unnecessary. The OS kernel and terminal are part of the execution environment.

Python, TypeScript and JavaScript support are user-authorized exceptions. Normal Python/npm packages and source examples use their language runtimes; static distribution, standalone executables, static ELF checks and CentOS validation are not required. Document supported runtimes/versions/dependencies and verify installation/import/execution in clean external environments. [Python TVR-15](https://leechis7.atlassian.net/browse/TVR-15) · [TypeScript/JavaScript TVR-16](https://leechis7.atlassian.net/browse/TVR-16).

Shell currently provides interpreter-based references. Any future independent Shell executable must follow the default static-distribution requirements. The build/ELF/CentOS commands below target static Go/Rust distribution.

## Build

The default build produces one Linux ARM64 artifact; choose other targets explicitly. Go requires 1.24+, Rust examples require 1.88+, and build tools require Python 3.

```sh
make build                    # bin/go/tuivory-linux-arm64, CGO_ENABLED=0
rustup target add aarch64-unknown-linux-musl
make build-rust               # bin/rust/tuivory-linux-arm64

# Requested CentOS 7.4 x86_64 target
make build-go-x86_64           # bin/go/tuivory-linux-x86_64
rustup target add x86_64-unknown-linux-musl
make build-rust-x86_64         # bin/rust/tuivory-linux-x86_64
```

Rust uses rustup's musl standard library and the host toolchain's bundled `rust-lld`. No separate GNU target linker or target glibc is needed. These are development tools, not executable runtime dependencies. Both languages select the UI language with `--lang ko|en`.

Builds check the ELF architecture and reject `PT_INTERP` and `DT_NEEDED`. Rust static PIE may retain `PT_DYNAMIC` for self-relocation. ELF checks and execution checks complement each other: even statically linked code can open runtime files. Check any additional dependencies in the final host application too.

```sh
python3 tools/check_static_elf.py --arch x86_64 bin/go/tuivory-linux-x86_64 bin/rust/tuivory-linux-x86_64
python3 tools/check_go_module.py --static-output /tmp/tuivory-go-consumer
python3 tools/check_rust_module.py --ratatui --static-output /tmp/tuivory-rust-consumer
```

External host checks use the standalone Go module and packaged Rust crate without the repository's shared design directory. They check public APIs and rendering, then export static x86_64 executables.

## Historical CentOS kernel validation (no longer performed)

Docker exports a root filesystem from a pinned official CentOS 7.4.1708 AMD64 image. QEMU boots the actual CentOS 7.4 `3.10.0-693.el7.x86_64` kernel. A container sharing a modern host kernel alone does not establish kernel compatibility. The guest glibc is `2.17-196.el7`. The VM runs without networking, KVM or host binfmt registration.

Docker, `qemu-system-x86_64` and BIOS files are required. Download the kernel from the [official CentOS archive](https://vault.centos.org/7.4.1708/os/x86_64/isolinux/vmlinuz); the script checks its SHA256. Both the image digest and kernel hash are pinned in `tools/check_centos74.py`.

```sh
curl --fail --location https://vault.centos.org/7.4.1708/os/x86_64/isolinux/vmlinuz -o /tmp/tuivory-centos74-vmlinuz
python3 tools/check_centos74.py --kernel /tmp/tuivory-centos74-vmlinuz \
  --binary go=bin/go/tuivory-linux-x86_64 \
  --binary rust=bin/rust/tuivory-linux-x86_64 \
  --consumer go-host=/tmp/tuivory-go-consumer \
  --consumer rust-host=/tmp/tuivory-rust-consumer
```

Checks cover Korean/English startup, Ctrl+Q exit, alternate-screen restoration and external host APIs/rendering. Add Tree/workspace examples using additional `--binary` arguments. Physical servers, SSH, user terminals and LazyOra/LazyBeaver integration remain separate checks. ARM64 static artifacts are checked separately; x86_64 results do not establish ARM64 CentOS compatibility. See the [validation record](../evidence/static-build.en.md).

## Publication status

These static builds are included in the v0.2.0 tagged release. The existing `v0.1.0` Rust ARM64 release binary uses GNU/glibc 2.39 and differs from the new static artifacts. Existing tags and assets have not been changed. The previous Go ARM64 artifact is already static but is not a CentOS 7.4 x86_64 artifact. Record new commits, publication and remote CI results separately.
