# Tuivory 0.10.1 릴리스

**한국어 (기본)** · [English](release-0.10.1.en.md)

Go·Rust auto/solid 팝업 그림자를 **오른쪽 1칸·아래 반 줄**로 통일했습니다. 테두리와 기본 끄기는 유지하며, 비교한 무테·오른쪽 전용 형태는 적용하지 않습니다. 다크는 실제 뒤쪽 배경의 RGB 40%, 라이트는 80% 밝기를 기준으로 대비를 확보하고 검정 배경·저색상 단말에는 대체 표현을 사용합니다.

```sh
go get github.com/leechis7/tuivory/go@v0.10.1
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.1", features = ["ratatui"] }
```

공개 API 이름은 유지합니다. 기본 그림자 할당 폭은 1칸 줄어드므로 반환한 Card/Bounds로 배치·입력을 판단하세요. 반 줄도 터미널 배치에서는 1행을 예약합니다. 반 블록은 배경 글자를 대체하며 ASCII는 점을 사용합니다. Dim은 일반 예제 순환에서 제외한 셀 전체 호환 모드입니다. [API·전환 상세](popup-shadows.md).

Go 1.24+, Rust 코어 1.85+, UI/예제 1.88+입니다. Rust는 Git 배포이며 crates.io에 게시하지 않습니다. Linux ARM64/x86_64 압축파일에는 언어별 정적 실행파일 하나를 포함하고 각 아키텍처의 실제 호스트에서 빌드합니다. [예제](examples.md) · [정적 빌드](static-build.md).

```sh
./bin/go/tuivory-linux-arm64 --demo menu --shadow auto --lang ko
./bin/rust/tuivory-linux-arm64 --demo menu --shadow auto --lang ko
```

[TVR-29 로컬 근거](evidence/tvr29-shadow-results.json)는 배포 전 이력으로 보존합니다. 12팔레트에서 Show/TestBackend의 두 칸 문자·반 블록·대비, PTY 입력·외부 패키지·정적 실행파일을 검사했습니다. 최종 배포 자산의 RELEASE-MANIFEST.json·SHA256SUMS에는 소스 일치·main CI·공개 태그 설치·다운로드 실행 근거를 기록합니다. CentOS·물리 폰트/SSH·실제 적용 앱의 업무 연결은 검증하지 않습니다. [배포 파일](https://github.com/leechis7/tuivory/releases/tag/go/v0.10.1).
