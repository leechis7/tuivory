# Tuivory work rules

[한국어 (default)](AGENTS.md) · **English**

- Keep the repository root language-neutral. Go source, go.mod, and go.sum belong in go/; shared themes, tokens, and specifications in design/. Keep Rust source, Cargo.toml, and Cargo.lock in rust/. Keep Python, JavaScript, and Shell implementations in their language directories.
- Tuivory is independent of LazyOra. Track its work in Jira project TVR. Do not create Tuivory tasks in LORA or continue reusing LORA-69.
- Check related Tuivory work before starting. If there is no issue, ask the user before creating one. If the project does not exist, do not substitute a LORA issue while waiting for project creation.
- Move the TVR issue to in progress when actual work starts. After implementation and required validation, complete it and add evidence in a comment. Distinguish local checks from unrun GitHub CI and publication state.
- Commit and publish to GitHub only after explicit user approval for the change. Write commit message descriptions in Korean.
- Use the actual created TVR issue key in branch names; do not invent numbers. Finish current work before starting another feature branch.
- The default local product build is one Linux ARM64 binary through make build. Other local operating systems/architectures require a user request.
- Put playground build outputs in `bin/<language>/`, with OS and architecture in the filename. Go uses `bin/go/tuivory-linux-arm64`; the explicit `make build-rust` target uses `bin/rust/tuivory-linux-arm64`. Executables for future languages follow the same convention. Python, JavaScript, and Shell run from source by default.
- Only the user decides the product major version.
- Create and update documentation in Korean and English together. Keep Korean as default, provide `.en.md` counterparts, and link them reciprocally. Align usage, support scope, and validation results. UI images use their document's language.
- For feature additions, changes, and bug fixes, update affected READMEs, usage/API guides, examples, UI images, and changelog in the same task. Update Korean and English together and confirm implementation/documentation/validation agreement before completing work.
- Keep the playground database-free and the style principles general. Do not pull LazyOra/Oracle internals into the shared core. Connect cross-project application examples through source links.

- Distributed executables for Go, Rust and future languages without an explicit exception must be static artifacts requiring no dynamic loader, shared libraries or separately installed language runtime. Those packages must not introduce mandatory native dependencies that prevent host static linking. Build-time modules/crates are allowed. Verify static Linux artifacts through ELF inspection and target OS/kernel execution. Shell sources are interpreter-based references; standalone executable distributions must meet the same static requirements. [Static distribution](docs/static-build.en.md)

- Python, TypeScript and JavaScript support are user-authorized exceptions. Deliver normal Python/npm packages and examples using their language runtimes. Static linking, standalone executables, static ELF checks and CentOS validation are not required. Document supported runtimes/versions/dependencies and verify installation/import/execution in clean external environments. [Python TVR-15](https://leechis7.atlassian.net/browse/TVR-15) · [TypeScript/JavaScript TVR-16](https://leechis7.atlassian.net/browse/TVR-16)

- After user approval, publish and merge each component stage into `dev` only. Update `main`, tags and Releases only after all work is complete and a separate release instruction is given. Do not automatically synchronize `main` and `dev` during stage publication.

- Tuivory is a TUI component library. Provide reusable controls, internal interaction/drawing and configurable layout tools; hosts own whole screens, cross-component focus order, global keys, menu/help content and business bindings. Normal host composition is not an incomplete migration defect. [Boundary](docs/component-boundary.en.md)
