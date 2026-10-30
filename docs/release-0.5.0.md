# Tuivory 0.5.0 릴리스

**한국어 (기본)** · [English](release-0.5.0.en.md)

Go·Rust 공통 팝업 그림자와 API Deprecated 안내를 제공합니다. 게시·검증 결과는 GitHub Release의 manifest로 확인합니다.

- [팝업 그림자](popup-shadows.md): 기본 끄기, Auto·Solid·Dim, 기본 오른쪽 2칸·아래 1행. Auto는 True Color/256색에서 은은한 명암을 사용합니다. 그림자는 입력 대상에서 제외하고 두 칸 문자 경계를 보호합니다.
- [API 지원 상태](api-lifecycle.md): Go 6개·Rust 4개 중복 API를 Deprecated로 표시하고 대체 방법을 안내합니다. 기존 동작을 보존하며 Rust 메뉴 생성자를 제공합니다.
- 한영 실행 예제·12팔레트 이미지·디자인/사용법을 갱신했습니다. Dim의 실제 밝기는 단말에 따라 달라집니다.

```sh
go get github.com/leechis7/tuivory/go@v0.5.0
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.5.0", features = ["ratatui"] }
```

Go 1.24+, Rust 코어 1.85+, UI/예제 1.88+입니다. Linux ARM64·x86_64의 Go/Rust 정적 playground·catalog·menu, Rust crate, SHA256SUMS와 RELEASE-MANIFEST.json을 배포합니다. 메뉴 예제는 `--shadow auto`와 F6으로 그림자를 선택합니다. CentOS 검증은 수행하지 않습니다. TVR-7 에픽은 열린 상태로 유지합니다.
