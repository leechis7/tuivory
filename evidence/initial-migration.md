# Tuivory 초기 이전 검증

**한국어 (기본)** · [English](initial-migration.en.md)

2026-10-24 · Linux ARM64 · 첫 배포 대상 0.0.1 · [TVR-2](https://leechis7.atlassian.net/browse/TVR-2)

이 문서는 초기 배포 당시의 검증 기록이므로 아래 실행파일 경로는 당시 기준입니다. 현재 Go 빌드 경로와 실행 명령은 [견본 안내](../docs/playground.md)를 따릅니다.

## 이전 범위

독립 저장소의 초기 구성으로 공통 design/, 언어별 디렉터리, Go 내부 구현·공개 API·DB 없는 견본을 정리했습니다. 제품·패키지·명령·토큰 초안 이름은 tuivory입니다. LazyOra 작업 트리는 수정하지 않았습니다. 원출처와 저작권은 [NOTICE](../NOTICE.md)에 보존합니다.

원본 CSV, LazyOra 출처 manifest·240색상·1572스타일 fixture, 라이선스와 의존성 체크섬은 기존 소스와 바이트 단위로 같습니다. 공통 토큰과 Go embed 사본은 형식 식별자를 제외한 색상·역할 데이터를 유지합니다.

## 로컬 검증

- `make test`: Go race 및 Python 3개 검사 통과. 원본 스타일 비교, 위젯·상태 보존 검사 포함.
- `make check`: Go vet, 192색상쌍 참조, 토큰 사본·CSV 일치, 로컬 문서 링크와 Shell 구문 통과.
- `make build`: Linux ARM64 바이너리 `bin/tuivory-linux-arm64` 생성.
- `make check-consumers`: Go/Python/Node.js의 12팔레트·192쌍 결과 일치.
- `python3 tools/check_go_module.py`: go/ 단독 테스트 및 외부 프로젝트의 공개 API·내장 토큰 검사 통과. 로컬 replace를 사용한 검사.
- `python3 tools/smoke_playground.py bin/tuivory-linux-arm64`: 실제 PTY 시작·Ctrl+Q 1회 종료·대체 화면 복원 통과.
- 실제 위젯으로 dark/light/blackwhite/팝업 SVG를 재생성하고 XML 검사 통과.
- 저장소 루트에 go.mod가 없고 모든 Go 소스가 go/ 아래에 있는지 확인.

임시 이전 디렉터리가 Git 저장소가 되기 전 빌드의 VCS 메타데이터 탐색이 실패했습니다. 새 저장소를 초기화한 뒤 동일한 기본 빌드·언어 간 데이터 비교 검사가 통과했습니다. 제품 코드나 빌드 검사를 우회하지 않았습니다.

## 검증 범위

위 결과는 로컬 검증입니다. GitHub CI·태그·Release·Go 프록시를 통한 replace 없는 외부 프로젝트 사용 결과는 배포 일감 댓글에 별도로 기록합니다. 실제 SSH 단말·사용자 ANSI 팔레트 전체 호환성이나 Python/JavaScript/Shell UI 패키지 완성을 뜻하지 않습니다.

## 게시·배포 결과

- 배포 커밋: `cf06d95f4334f65436197ae4f12faf35783f5b7a`.
- [원격 CI](https://github.com/leechis7/tuivory/actions/runs/40057059473)의 validate/go-package 모두 성공.
- [Tuivory v0.0.1 Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.0.1), Go 태그 `go/v0.0.1` 게시.
- 저장소 밖 새 사용 예제 모듈에서 `GOWORK=off GOPROXY=https://proxy.golang.org go get github.com/leechis7/tuivory/go@v0.0.1` 성공. 로컬 replace 없이 12테마·프로필 조합 스타일, 입력 상태 보존, 내장 토큰 형식·팔레트 해석 검사 통과.
- 모듈 체크섬: `h1:5xsN+SnSOgwVFGheRzCaS7CXsq6waPiW3+FIKjZTUAg=`.

자동 GitHub 개발 활동 연동의 관리 설정은 도구 접근 범위 밖입니다. 사용자에게 GitHub for Atlassian의 선택 저장소에 tuivory를 추가하는 경로를 안내했고, Jira에는 저장소·CI·Release Web links를 등록했습니다. Web links 등록을 자동 연동 완료로 간주하지 않습니다.
