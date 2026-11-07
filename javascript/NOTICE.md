# Tuivory TypeScript / JavaScript — 출처 안내

**한국어 (기본)** · [English](NOTICE.en.md)

이 언어 구현은 Tuivory의 AGPL-3.0-only 독립 구현이며 다른 Tuivory 언어 구현을 링크하거나 호출하지 않습니다.

Unicode 폭·grapheme 데이터와 폭 처리 알고리즘은 wcwidth 0.9.4(Unicode 18.0.0)의 데이터에서 생성했으며 MIT와 Markus Kuhn 출처를 보존합니다. [UNICODE-LICENSE](UNICODE-LICENSE)와 design/ 원본을 참고하세요. Python은 일반 regex/wcwidth 의존성을 사용하며 다른 언어는 자체 폭·분할 구현과 내장 데이터를 사용합니다.

검색의 대소문자 매핑은 Unicode17 기본 full C+F 데이터를 [Unicode License V3](CASEFOLD-LICENSE)로 내장합니다. Turkic 예외와 정규화는 적용하지 않습니다. 원본 URL·해시는 design/casefold.json에 보존합니다.

SQL 문자 분류는 Unicode17.0.0의 Alphabetic·일반 범주 N·White_Space 데이터를 [Unicode License V3](CASEFOLD-LICENSE)로 내장합니다. 공식 원본 URL·해시는 design/syntax-unicode.json에 보존합니다. 생성된 표와 강조용 단어 목록은 공통 데이터이며 각 언어의 분석기는 독립 구현합니다.
