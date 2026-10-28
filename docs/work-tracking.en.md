# Tuivory work tracking

[한국어 (default)](work-tracking.md) · **English**

Tuivory is independent. Its Jira project is named **Tuivory**, with key **TVR**. Check the actual TVR issue before feature or documentation work.

| Issue | Scope | Validation and publication |
| --- | --- | --- |
| [TVR-1](https://leechis7.atlassian.net/browse/TVR-1) | Foundation and evidence | Complete; initial implementation and attribution preservation verified |
| [TVR-2](https://leechis7.atlassian.net/browse/TVR-2) | Independent repository and first Go release | Complete; [CI](https://github.com/leechis7/tuivory/actions/runs/40057059473), [go/v0.0.1 Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.0.1), external project use through the Go proxy passed |
| [TVR-3](https://leechis7.atlassian.net/browse/TVR-3) | Korean/English documentation and synchronization policy | Initial guides merged and published in [PR #1](https://github.com/leechis7/tuivory/pull/1); subsequent full refresh completed 29 Korean/English pairs and local validation; follow-up publication and CI results are recorded in TVR-3 comments |
| [TVR-4](https://leechis7.atlassian.net/browse/TVR-4) | Playground language selection and English images | Complete; Korean/English UI, four English images, PTY checks for both languages; merged and published in PR #1 |
| [TVR-5](https://leechis7.atlassian.net/browse/TVR-5) | Rust ecosystem epic | In progress. Core, Ratatui adapter, bilingual interactive example, isolated packaging, documentation and images implemented/validated locally. Rust Git tag rust/v0.1.0 distributed. Actual LazyBeaver integration is separate; see issue comments for CI/publication evidence |
| [TVR-6](https://leechis7.atlassian.net/browse/TVR-6) | Go module epic | Remains open. Go go/v0.1.0 includes per-language output paths and shared APIs; see issue comments for CI/publication evidence |
| [TVR-7](https://leechis7.atlassian.net/browse/TVR-7) | Go/Rust shared UI epic | In progress. Support audit, Tree, tabs, panels/splitters, status and breadcrumbs implemented, validated and committed locally in both languages. Distributed in v0.1.0; see comments for CI/publication evidence; real integration is separate |

PR #1 merged as `5c3242ff17c719d7558d447c93477234f75fe698`. Both [dev CI](https://github.com/leechis7/tuivory/actions/runs/40062239810) and [main CI](https://github.com/leechis7/tuivory/actions/runs/40062241916) passed. This merge did not create a new tag or Release; the Go version at that time was `v0.0.1`; the current version is `v0.2.0`.

Integration branches are `main` and `dev`; work branches use `codex/actual-TVR-key-description`. The workflow is to do → in progress → review → done, with one task at a time. Feature changes include related documentation updates in Korean and English. Distinguish local checks, remote CI, publication, and tagged releases. Commits and GitHub publication require explicit approval for the change.

Local validation for subsequent work is recorded in its TVR issue comments. Successful CI for the earlier PR does not validate subsequent local changes.

Automatic GitHub development activity depends on GitHub for Atlassian repository access settings. Manual source links do not establish automatic integration. See the [roadmap](roadmap.en.md) for unimplemented language UI packages and real terminal validation.

## Static distribution follow-up

TVR-5/TVR-6 now cover static distribution and host-linking requirements for Go, Rust and future languages. CentOS 7.4 x86_64 guest-kernel/external-host/bilingual playground checks and local ARM64 checks passed. See [evidence](../evidence/static-build.en.md). Source publication is authorized. Record remote CI, PR and merge results in TVR-5/TVR-6 comments; existing v0.1.0 tags/assets remain unchanged. Epics remain open.

## Shared component expansion backlog

TVR-8–13 were registered under TVR-7 in the approved order and all completed dev integration and remote CI. See [scope/order/publication checkpoints](components-backlog.en.md). TVR-14 Go overlay repairs also merged into dev through PR #13. Each issue records PR/CI/merge evidence; keep the epic open. These changes are now included in 0.2.0 preparation.

On 2026-10-28 the user limited stage integration to `dev`. Validate and merge TVR-8 from its existing branch into dev; leave main/tags/Releases unchanged until a separate release instruction after all work. Record PR/CI evidence in TVR-8 comments.

## TVR-9–13 completion

The user explicitly authorized sequential implementation, commits and dev merges through TVR-13. All five stages provide public APIs, bilingual docs/hosts/references and local checks; PR/final-dev CI and merge commits are recorded per issue. Main/tags/releases remain unchanged until a separate release instruction. Keep TVR-7 open.

## 0.2.0 release

The user approved full publication after preparation. Include TVR-8–14/static changes, validate dev/main, tag the same commit with go/v0.2.0 and rust/v0.2.0, rebuild assets from that commit, and verify real tag installation/downloads. Record actual PR/CI/publication evidence in TVR-7 and TVR-5/6 comments. Keep epics open. [Release guide](release-0.2.0.en.md).
