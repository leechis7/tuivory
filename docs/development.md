# 개발·검증·이력

**한국어 (기본)** · [English](development.en.md)

조사·검증 기록은 작성 당시 버전을 설명합니다. 현재 앱 개발에는 설치 안내와 API 명세를 사용하세요.

로컬 실행파일은 `bin/go/`·`bin/rust/`에 하나씩 유지하고, 빌드·검증 임시 산출물과 로컬 릴리스 보관은 Git 제외 `.cache/`에 둡니다. Rust 기본 출력은 `.cache/rust/`입니다. [현재 폴더 구조](architecture.md).

- [구조](architecture.md)
- [기여](../CONTRIBUTING.md)
- [작업 관리](work-tracking.md)
- [로드맵](roadmap.md)
- [컴포넌트 점검](component-audit.md)
- [백로그](components-backlog.md)
- [정적 배포](static-build.md)
- [검증 기록](evidence/README.md)
- [배경 조사](background-audit.md)
- [API 중복 점검](api-overlap-audit.md)
- [그리드 검증](grid-validation.md)
- [추출 출처](lazyora-extraction.md)
- [Go 범위](go-style-coverage.md)
- [참고 자료](sources.md)
- [변경 이력](../CHANGELOG.md)

릴리스: [0.5.0](release-0.5.0.md) · [0.4.0](release-0.4.0.md) · [0.3.0](release-0.3.0.md) · [0.2.0](release-0.2.0.md)
