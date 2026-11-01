# 언어 중립 강조 분석 규격

**한국어 (기본)** · [English](syntax.en.md)

0.9.0 TVR-24 규격입니다. [사용법·실행 예제·편집기 전환](../docs/syntax.md) · [공통 fixture](syntax-cases.json) · [공유 SQL 사전](sql-syntax-words.json). SDK 구현 언어와 분석 대상 언어는 서로 독립적입니다.

| 계층 | SDK 책임 | 앱 책임 |
| --- | --- | --- |
| 토큰 | 원문 UTF-8 byte [start,end), 의미 역할, 언어/방언, 원문 동일성 검사 | 원문·언어/방언 선택 |
| 선택 분석기 | Oracle SQL/PLSQL lexer, 자체 분석기 주입 API | 자체 분석기·작업 스레드/스케줄링 선택 |
| 렌더러 | grapheme 변환, 셀 폭·CJK, 팔레트, 상태·스크롤·편집 | 화면 조합·전역 키·검색 쿼리 |
| 업무 | 없음 | 실행/위험 SQL·트랜잭션·DB/Oracle 메타데이터 |

기본 core는 모든 언어 분석기를 필수로 요구하지 않습니다. Go는 루트 API 호출로 선택하며 사전 초기화는 생성 시에만 수행합니다. Rust syntax-sql 기능은 기본값 꺼짐이며 렌더링 기능과 독립적입니다. 새 런타임·네이티브 도구·DB 의존성은 없습니다. Python/JS/TS/C/C++ 어댑터도 동일한 값 규격을 사용할 수 있도록 유지합니다.

## 토큰과 적용

source는 원문 그대로이며 토큰은 정렬된 비중첩 양의 길이 byte 범위입니다. 공백 생략을 허용합니다. 렌더러가 원문에 태그를 삽입하지 않습니다. 공급 결과는 원문과 범위를 검증하고 원자적으로 적용합니다. 기존 SetByteSyntax는 엄격한 grapheme 경계 변환을 유지합니다. 내장 분석기는 grapheme에 처음 겹친 토큰의 역할을 cluster 전체에 적용합니다. 이는 UTF-8 바이트·grapheme·셀 좌표를 혼용하는 것이 아닙니다.

초기 분석기 설정 실패는 이전 설정을 보존합니다. 편집 후 실패는 오래된 강조를 비우고 오류를 노출합니다. 같은 실패/성공 원문은 재사용하며 원문 변경 또는 명시적 재설정에 재분석합니다. 적용·콜백은 UI 실행 흐름에서 수행합니다. 앱이 비동기 분석을 선택하면 원문을 가진 결과를 다시 전달하며 stale 결과는 거부합니다. 비밀 상태에는 자동 분석을 실행하지 않고 진단 캐시를 노출하지 않습니다.

## 역할과 fallback

| 의미 역할 | 렌더링 가족 | 기존 팔레트 전경 |
| --- | --- | --- |
| keyword | syntax.keyword | info |
| function, macro, attribute | syntax.function | success |
| type | syntax.type | header |
| string, character | syntax.string | warning |
| number, constant | syntax.number | edited |
| comment, directive | syntax.comment | hint |
| parameter, lifetime | syntax.parameter | error |
| identifier, operator, punctuation, 미지원 역할 | body | body |

전경은 대비 규칙을 거쳐 실제 surface 배경과 결합합니다. 언어별 새 팔레트는 만들지 않습니다. 기존 Go 7종 SyntaxKind 숫자는 유지합니다. 0.9.2는 다크/8색의 색상·속성 조합을 개선하며 기본 Go/Rust 편집기와 SyntaxStyleFunc에 같은 원칙을 적용합니다. 우선순위는 비활성 > 선택 > 검색 일치(edited) > 문법 > 본문이고, 커서는 선택된 배경을 유지하며 포커스 표시를 더합니다. 원문 변경은 검색 결과를 만료시킵니다. 다크/라이트/흑백 × 8/16/256/True Color, Unicode/ASCII를 같은 원칙으로 처리합니다.

## 현재 구현: Oracle SQL/PLSQL

키워드·알려진 내장 함수·자료형·일반/N/q/nq 문자열·숫자·주석·바인드와 식별자/연산자/구두점을 분류합니다. quoted identifier는 identifier이며 문자열/주석 안의 키워드는 재분류하지 않습니다. PL/SQL 주석은 Oracle의 비중첩 블록 종료 규칙을 따릅니다. 미완성 문자열/주석은 남은 원문 전체를 해당 역할로 보존합니다. SQL 사전은 고정된 강조용 최소 집합으로 스키마·버전 전체나 의미 분석을 보장하지 않습니다. 알 수 없는 이름을 함수·자료형으로 추측하지 않습니다.

[Oracle 문자열/숫자 규칙](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Literals.html) · [PL/SQL 어휘 규칙](https://docs.oracle.com/en/database/oracle/oracle-database/21/lnpls/plsql-language-fundamentals.html). SQL 실행 안전성 검증과 무관한 자체 AGPL-3.0-only 구현입니다.

## 후속 source 언어 분류 기준: 아직 분석기 없음

| 언어 | 최소 규칙 |
| --- | --- |
| Go | func/package/if는 keyword. 호출/알려진 builtin은 function, 타입 위치의 int/string·선언 타입은 type. 변수명은 identifier, true/false/nil은 constant. 일반/백틱 문자열은 string, rune은 character, 정수/실수/허수는 number. 줄/블록 주석은 comment, //go:build는 directive. 문맥을 알 때 인자명은 parameter, 아니면 identifier. |
| Rust | fn/let/impl/match는 keyword. 문맥상의 호출·자료형, 변수/raw identifier는 identifier. true/false는 constant. 일반/raw/byte 문자열은 string, 문자/byte 문자는 character. 중첩 블록/줄 주석은 comment, println!은 macro, derive 등은 attribute, &'a의 'a는 lifetime이며 문자와 구별. |

제네릭·raw/멀티라인 문자열·주석 속 가짜 키워드·미완성 입력을 후속 fixture 기준으로 둡니다. 현재 SQL 분석기에 Go/Rust를 요청하면 오류이며 계획을 구현 완료로 표시하지 않습니다. 향후 언어를 추가할 때 동일한 역할/범위/fallback·원문/Undo/Redo/선택·성능 검증을 확장합니다.

## 검증·성능

공통 fixture는 현재 SQL 토큰의 정확한 byte/역할, 모든 UTF-8 경계의 미완성 입력, 17개 역할 fallback과 후속 언어 예제를 구분합니다. Go/Rust에서 같은 fixture를 사용합니다. 1만 줄 분류·적용·원문 보존 및 스크롤을 검증하고 실제 측정값은 [검증 기록](../docs/evidence/syntax-results.json)에 남깁니다. 전체 분석/전체 Layout이며 증분 처리·rope는 아닙니다. Go Show/Rust TestBackend와 실제 PTY 검증·미실행 원격 CI/게시는 구분합니다.

0.9.2의 다크/8색은 참조 대비 >=4.5:1인 7종 전경·속성 조합을 Go/Rust 기본 렌더러와 Go 기존 어댑터에 공통 적용합니다. 역할별 표현과 단말 제약은 [사용법](../docs/syntax.md)을 참고하세요.
