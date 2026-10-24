# 공식 참고 자료와 유래

최초 조사일: 2026-10-23. 프레임워크 문서는 API/버전이 바뀔 수 있으므로 실제 어댑터 구현 시 다시 확인합니다. 아래 자료는 설계 참고이며 해당 프로젝트가 이 가이드를 승인했다는 뜻은 아닙니다.

| 출처 | 참고한 부분 |
| --- | --- |
| [Textual Themes](https://textual.textualize.io/guide/design/) | 테마 변수, 위젯별 스타일과 글자/배경 역할 |
| [Lip Gloss](https://github.com/charmbracelet/lipgloss#advanced-color-usage) | 출력 능력에 맞는 명시적 색상 선택 |
| [Ratatui 색상 예제](https://www.ratatui.rs/examples/style/colors/) | 실제 위젯에서 색상 프로필 비교 |
| [Carbon 색상 지침](https://www.carbondesignsystem.com/building-blocks/foundations/color/guidelines) | 의미별 토큰과 레이어/상태 |
| [DTCG 2025.10](https://www.designtokens.org/tr/2025.10/format/) | 토큰·타입·별칭 개념. 이 가이드는 해당 형식의 완전 호환 구현이 아님 |
| [WAI 키보드 지침](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/) | 포커스/선택 구분, 영역 간/내부 이동 |
| [WAI 모달 지침](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) | 모달 입력 차단과 포커스 복귀 |
| [W3C 색 사용](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [대비 설명](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) | 색 외의 의미 전달과 대비 조사 참고 |
| [xterm 공식 문서](https://www.invisible-island.net/xterm/manpage/xterm.html) | boldColors와 기본 전경색의 밝은색 변환 |

웹의 ARIA/CSS를 터미널에 구현했다거나 WCAG 인증을 받았다는 뜻은 아닙니다. 외부 문서 전문을 복제하지 않고 링크와 직접 작성한 적용 판단을 남깁니다.

## 초기 자료의 원본

[LazyOra](https://github.com/leechis7/lazyora) LORA-69에서 출발했습니다. 원본 기준 커밋은 [a38c46e](https://github.com/leechis7/lazyora/commit/a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7)입니다.

- `docs/tui-style-guide/principles.md` → 공통 원칙.
- `docs/ui-style-palette-candidate.csv` → 검토용 테마 예시.
- `shell/examples/terminal-colors.sh` → 단말 색 견본.
- `tools/theme_audit.py`의 대비 계산 방법 → 독립 팔레트 검사기로 재구성.

앱 위젯 캡처 하네스·Go Oracle 코드·대용량 화면 갤러리는 이 저장소에 이관하지 않았습니다. 앱에 종속된 검사와 독립 도구를 구분하기 위해 사례 링크만 제공합니다. 라이선스와 유래는 [NOTICE](../NOTICE.md)를 참고하세요.
