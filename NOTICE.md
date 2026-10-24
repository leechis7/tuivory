# 유래와 라이선스

Copyright (C) 2026 Chaekang Lee

이 프로젝트의 초기 문서·테마 예시·단말 색 견본은 [LazyOra](https://github.com/leechis7/lazyora) LORA-69 작업에서 파생되었습니다. 개발자: 이채강 (Chaekang Lee), leechis7@gmail.com.

원본 기준: [a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7](https://github.com/leechis7/lazyora/commit/a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7).

문서 링크와 프로젝트 경계를 독립 저장소에 맞게 재구성하고, 참조 팔레트 검증 도구를 추가했습니다. 기존 AGPL-3.0-only 조건을 유지하며 임의로 재라이선스하지 않았습니다. 전체 조건은 [LICENSE](LICENSE)를 확인하세요.

공식 참고 문서는 [출처 목록](docs/sources.md)으로 연결합니다. Textual·Lip Gloss·Ratatui·Carbon·W3C 등의 문서 전문이나 구현 라이브러리를 번들하지 않았으며 해당 프로젝트의 이름은 출처를 식별하기 위해 사용합니다.

실행형 견본은 stock tview/tcell을 Go 모듈로 사용하며 LazyOra의 로컬 tview 포크를 포함하지 않습니다. 선택 목록이 기존 한글 2셀 문자와 겹칠 때의 경계 처리 방법은 LazyOra의 사례를 적용했습니다. 의존성 버전은 go/go.mod·go/go.sum에 기록합니다.

LazyOra의 실제 테마·스타일 함수에서 파생한 Go 패키지를 추가했습니다. 원본 커밋·파일 해시·추출 범위는 [추출 기록](docs/lazyora-extraction.md)에 남겼으며 기존 AGPL-3.0-only 조건을 유지합니다.

## Tuivory 이전

Tuivory는 [TUIS](https://github.com/leechis7/tuis)의 구현과 언어 중립 구조 전환 작업을 바탕으로 새 저장소에서 시작합니다. 기존 저작권·AGPL-3.0-only 조건과 LazyOra 원본 스타일 출처는 유지합니다. 이전 요약은 [전환 안내](docs/migration.md)를 참고하세요.
