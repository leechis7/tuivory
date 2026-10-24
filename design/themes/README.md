# 테마 후보와 참조 검사

**한국어 (기본)** · [English](README.en.md)

[lazyora-candidate.csv](lazyora-candidate.csv)는 LazyOra 설계 단계에서 작성한 **12프로필 × 16역할, 192개 전경/배경 쌍**의 예시입니다. 배포된 LazyOra의 현재 팔레트를 그대로 덤프한 파일도, 모든 TUI에 적용할 표준색도 아닙니다.

| 열 | 의미 |
| --- | --- |
| profile | 테마와 표현 능력, 예: dark-8 / light-256 / blackwhite-truecolor |
| role | 의미별 역할 |
| foreground / background | 인덱스 또는 True Color의 #RRGGBB |
| reference_fg / reference_bg | 참조 팔레트로 해석한 RGB |
| contrast | 일반 글꼴 모델에서 계산한 참고 대비 |
| target | 해당 역할의 내부 검토 목표 |
| font_weight | none 또는 bold |

```sh
python3 tools/check_palette.py design/themes/lazyora-candidate.csv
```

검사기는 필수 열, 중복 역할, 색상 범위, RGB 참조값, 유한한 목표/대비, 계산 결과 및 Bold의 밝은색 모델을 확인합니다. 실패하면 종료 코드 1을 반환합니다. 제공된 192개 행을 반드시 가져야 한다는 일반 스키마를 강제하지 않으므로 사용자 테마의 일부 역할 표에도 사용할 수 있습니다.

일반 텍스트 4.5:1, 포커스 경계 3:1은 내부 설계 참고 목표입니다. CSV에서는 역할별 target을 명시하며, 검사 통과가 화면 전체의 접근성 인증을 의미하지 않습니다. 레이어 합성·커서·문자 폭·Dim·반전·동작은 별도 확인해야 합니다.

[공통 JSON 토큰 초안](../tokens/README.md)은 이 CSV에서 생성하며 Go·Python·Node.js가 함께 읽습니다. Go에는 토큰 로더와 tcell 스타일 어댑터가 있습니다. DTCG 확장과 완성 위젯 SDK는 아직 제공하지 않습니다. CSV와 초안 JSON을 향후 API 호환성 보장으로 해석하지 마세요.
