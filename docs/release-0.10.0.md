# Tuivory 0.10.0 릴리스

**한국어 (기본)** · [English](release-0.10.0.en.md)

40열 확인창에서 긴 버튼을 여러 행으로 배치하고 기본 취소 버튼과 포커스를 유지합니다. Go·Rust 탭과 트리에 기본 끄기의 드래그 앤 드롭을 제공하며, 앱이 승인한 요청에만 새 모델로 재정렬·부모 변경을 적용합니다.

```sh
go get github.com/leechis7/tuivory/go@v0.10.0
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.0", features = ["terminal", "syntax-sql"] }
```

Go 1.24+, Rust 코어 1.85+, UI/예제 1.88+입니다. Go는 루트 패키지 하나만 import하고 Rust는 tuivory 의존성만 선언합니다. Rust는 Git 배포이며 crates.io에 게시하지 않습니다.

- [반응형 Go Modal](modals.md): 작은 높이의 포커스 버튼 가시성·콜백/키보드/마우스·테마별 테두리 대비를 보완합니다.
- [Go/Rust 드래그 앤 드롭](drag-drop.md): 탭 순서와 트리 앞/뒤/자식 이동, 안정 ID·메타데이터·하위 트리 보존, 순환/비활성/잠금/정책/오래된 요청 차단, 영역 밖 캡처·취소·키보드 대안을 제공합니다. 미리 보기 스크롤/펼침은 실제 상태와 별도입니다.

Go `Modal`은 원시 backend 타입 별칭 대신 backend Modal을 내장한 SDK 어댑터입니다. `NewModal().SetText(...).AddButtons(...).SetFocus(...)` 같은 SDK 사용 방식은 유지합니다. 원시 backend 타입을 받는 외부 코드에는 `modal.Modal`을 전달할 수 있으나 그 객체를 직접 그리면 반응형 처리를 우회합니다. [상호 운용 안내](modals.md).

```sh
./bin/go/tuivory-linux-arm64 --demo controls --modal --lang ko --theme light --colors 8
./bin/go/tuivory-linux-arm64 --demo workspace --drag --lang ko
./bin/rust/tuivory-linux-arm64 --demo workspace --drag --lang en --ascii
```

[배포 파일](https://github.com/leechis7/tuivory/releases/tag/go/v0.10.0)은 Go/Rust Linux ARM64/x86_64별로 정적 실행파일 하나를 포함합니다. ARM64는 로컬 ARM64, x86_64는 GitHub x86_64 호스트에서 빌드하며 교차 빌드하지 않습니다. 실행파일은 `bin/<언어>/tuivory-linux-<아키텍처>`입니다. 별도 런타임·공유 라이브러리가 필요 없습니다. [전체 예제](examples.md) · [정적 빌드](static-build.md).

구현 단계의 [로컬 검증](evidence/tvr7-18-results.json)은 게시 전 이력으로 보존합니다. Modal 216개 크기/언어/팔레트 사례, Go/Rust 공통 이동·실제 출력 회귀, 한영 PTY 58개, 외부 패키지·Rust 코어 최소 버전과 정적 실행파일을 검사했습니다. 최종 RELEASE-MANIFEST.json·SHA256SUMS는 main CI·네 실행파일의 소스/정적 ELF/체크섬·공개 태그 설치·다운로드 실행 근거를 기록합니다. CentOS·물리 폰트/SSH·실제 적용 앱 업무 연결은 검증하지 않습니다. 기존 태그와 자산은 보존합니다.
