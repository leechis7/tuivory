# Withdrawn versions and upgrades

[한국어 (default)](withdrawn-versions.md) · **English**

**Do not use 0.10.1. Upgrade to 0.10.2 or later.** Importing the root Go facade on Windows references missing backend NewStdIoTty and fails compilation. Do not start new installs/builds/deployments with this version. The same defect is not reported in Rust, but the product 0.10.1 withdrawal applies to both language distributions.

The 0.10.2 Go module declares `retract v0.10.1` with a rationale. Normal latest-version selection excludes retracted versions; this cannot delete cached code or forcibly block explicitly pinned versions. GitHub Release is marked DO NOT USE and excluded from stable latest selection. Existing tags/archives remain historical reproduction/audit material, not recommended installation targets.

```sh
go get github.com/leechis7/tuivory/go@v0.10.2
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.2", features = ["ratatui"] }
```

A consuming Go application can forbid selecting 0.10.1 by adding this to **its own go.mod**. Unlike SDK retraction metadata, exclude is a dependency policy managed by the host.

```go
exclude github.com/leechis7/tuivory/go v0.10.1
```

[Fix details](ui-facade.en.md) · [0.10.2 release](release-0.10.2.en.md) · [TVR-26](https://leechis7.atlassian.net/browse/TVR-26)
