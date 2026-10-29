# 언어 독립 토큰 데이터

**한국어 (기본)** · [English](README.en.md)

[candidate.json](candidate.json)은 Go/Python/Node.js/Rust가 함께 읽는 참조 데이터이고 [schema.json](schema.json)은 JSON 구조를 설명하는 스키마입니다. 형식 식별자 `tuivory.tokens.draft`는 초안 구분자이며 제품 버전이 아닙니다. DTCG 호환이나 공개 API 안정성을 보장하지 않습니다.

```json
{
  "foreground": "7",
  "background": "0",
  "referenceForeground": "#c0c0c0",
  "referenceBackground": "#000000",
  "fontWeight": "none"
}
```

최상위 `roles`는 표시 순서, `palettes`의 키는 `dark-8`처럼 테마와 단말 능력의 조합입니다. 각 팔레트는 `roles`의 역할을 정확히 한 번씩 포함합니다. 기본 데이터는 3테마 × 4프로필 × 16역할입니다.

- `foreground`/`background`: 정규화된 십진 인덱스 문자열 또는 `#RRGGBB`. 8/16/256 프로필은 각각 0–7/15/255 인덱스만 사용합니다. truecolor는 RGB와 0–255 인덱스를 모두 사용할 수 있습니다.
- `referenceForeground`/`referenceBackground`: 검증에 사용하는 참조 RGB. ANSI 사용자 팔레트를 강제로 대체하는 값이 아닙니다.
- `fontWeight`: `none` 또는 `bold`. 굵기가 밝은색으로 변하는 단말은 별도로 검증합니다.

스키마는 구조를 검사합니다. 역할 집합의 일치와 프로필별 색상 범위는 추가 의미 검사가 필요하며 현재 Go의 `tuivory.ParseTokens`와 Rust의 `TokenDocument::from_json`이 수행합니다. JSON 객체의 속성명은 중복하지 않습니다.

## 참조 후보의 출처와 생성

현재 후보는 [원본 CSV](../themes/lazyora-candidate.csv)에서 생성합니다. CSV는 LazyOra 설계에서 유래한 검토 자료이며 모든 앱에 강제하는 기본 테마가 아닙니다. 해당 후보를 수정할 때에는 CSV를 수정한 뒤 아래 명령으로 JSON을 재생성합니다. 다른 테마를 추가할 때는 같은 형식의 독립 문서를 만들 수 있습니다.

```sh
python3 tools/export_tokens.py
python3 tools/export_tokens.py --check
```

공통 원본은 이 디렉터리의 JSON이며 Go 소스는 두지 않습니다. 생성 도구는 같은 내용을 `go/internal/tokens/candidate.json`과 `rust/src/data/candidate.json`에도 기록합니다. 이 생성 복사본은 Go·Rust 패키지의 독립 배포와 내장을 위한 것이며 수동 편집하지 않습니다. `--check`는 원본 CSV·공통 JSON·Go·Rust 배포 사본이 모두 같은지 확인합니다. Go·Rust 프로젝트는 저장소의 다른 디렉터리 없이도 사용할 수 있고 Python·JavaScript는 공통 원본을 직접 읽습니다.

원본 역할의 배경과 실제 컴포넌트 바탕은 구분합니다. 평문에 raw 역할의 배경을 그대로 덮지 않으며, 실제 표면 위 전경 대비도 확인합니다. 입력·선택·수정·사용자 배경은 보존합니다. [표면 규칙](../surfaces.md).
