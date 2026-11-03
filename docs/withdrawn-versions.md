# 사용 금지 버전과 업그레이드

**한국어 (기본)** · [English](withdrawn-versions.en.md)

**0.10.1은 사용 금지입니다. 0.10.2 이상으로 업그레이드하세요.** Windows에서 Go 루트 파사드를 import하면 backend에 없는 NewStdIoTty를 참조해 컴파일이 실패합니다. 이 버전으로 새 설치·빌드·배포를 진행하지 마세요. Rust에서 같은 결함이 확인된 것은 아니지만 제품 0.10.1의 사용 금지 안내는 동일하게 적용합니다.

0.10.2 Go 모듈은 `retract v0.10.1`과 사유를 제공합니다. Go의 일반 최신 버전 선택은 회수 버전을 제외합니다. 다만 이미 캐시한 코드나 명시적으로 고정한 버전을 강제 삭제하거나 실행 차단하지는 못합니다. GitHub Release도 사용 금지로 표시하고 정식 최신 대상에서 제외합니다. 기존 태그·아카이브는 재현과 감사를 위한 이력으로 보존하며 권장 설치 대상이 아닙니다.

```sh
go get github.com/leechis7/tuivory/go@v0.10.2
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.2", features = ["ratatui"] }
```

Go 적용 앱이 0.10.1 선택 자체를 금지하려면 **앱의 go.mod**에 다음을 추가할 수 있습니다. SDK의 retract와 달리 exclude는 적용 앱이 관리하는 의존성 정책입니다.

```go
exclude github.com/leechis7/tuivory/go v0.10.1
```

[수정 상세](ui-facade.md) · [0.10.2 릴리스](release-0.10.2.md) · [TVR-26](https://leechis7.atlassian.net/browse/TVR-26)
