# 검증 기록

**한국어 (기본)** · [English](README.en.md)

계산·시뮬레이션·실제 단말 확인을 구분합니다. 미확인 항목은 ‘미확인’이라고 기록하며 실제 호스트명·계정·암호·업무 데이터 대신 합성 데이터를 사용합니다.

```text
규칙/컴포넌트 ID:
가이드·테마·어댑터 버전 또는 커밋:
앱/위젯 버전, OS/아키텍처:
테마, 프로필, TERM/COLORTERM, 라이브러리가 보고한 색상 수:
단말 프로그램/버전, 로컬/SSH/tmux 등 경로:
ANSI 팔레트(참조/사용자 변경/미확인), 굵게 설정:
창 크기(열×행), 폰트, 언어:
전제 상태와 재현 순서:
기대 결과 / 실제 결과:
방법: 팔레트 계산 / 위젯 시뮬레이션 / 실제 단말
결과: 통과 / 실패 / 미확인, 예외:
자료 위치, 확인 날짜:
```

## 출발 사례: LazyOra LORA-69

[조사 기록](https://github.com/leechis7/lazyora/blob/a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7/docs/audits/lora-69.md) · [적용·검증 기록](https://github.com/leechis7/lazyora/blob/a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7/docs/audits/lora-69-implementation.md)

67장면×12조합×한영×초기/왕복 3,216프레임을 실제 앱 위젯의 tcell 시뮬레이션으로 비교한 사례입니다. 색상 값 치환이 테마 복원을 깨뜨리고, 폼의 입력 글자색이 읽기 전용 설명을 가리며, ANSI Bold가 선택 셀 대비를 떨어뜨린 문제에서 공통 원칙을 도출했습니다.

이 저장소에 앱의 Oracle 자료형·작업자·DB 시험 환경을 복사하지 않습니다. 앱 전용 캡처 하네스는 LazyOra에 남깁니다. Tuivory의 독립 견본·양 언어 SVG 생성은 [견본 안내](../docs/playground.md), 실제 실행 검사는 `tools/smoke_playground.py`로 제공합니다. 위 양식은 범용 관찰 기록에 사용합니다. 위 사례는 SecureCRT/MobaXterm의 실제 사용자 팔레트 확인 기록이 아닙니다.

## 정적 배포

[Go·Rust·CentOS 7.4 검증](static-build.md): 실제 구형 게스트 커널·외부 정적 앱·한영 UI와 ARM64 로컬 검사.

## 공통 상태·포커스·팝업

[TVR-8 검증](focus.md): 공통 계약·12팔레트·한영 PTY·외부 정적 앱·CentOS 7.4·한영 참조 이미지. 게시 전 로컬 검증 근거이며 원격 게시·CI 결과는 TVR-8 댓글에 따로 기록합니다.

[TVR-9~13 전체 컴포넌트 검증](components.md): 공개 API·행 소스·요청/수명·배치 경계·한영 PTY와 정적 외부 앱.
