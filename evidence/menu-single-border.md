# 단일선 메뉴 표시 검증

**한국어 (기본)** · [English](menu-single-border.en.md)

이 문서는 해당 단계의 과거 검증입니다. 이후 배경·비활성 표시 변경은 [후속 검증](background-fix.md)을 참고하세요.


TVR-7의 0.3.0 이후 미배포 변경입니다. 사용자 요청으로 메뉴만 별도 포커스 장식을 제거합니다. 기존 태그·Release 자산을 수정하지 않습니다. [표시 규칙](../docs/menus.md).

- Go: MenuView와 메뉴 바는 입력 포커스에 따른 밑줄을 추가하지 않습니다. NewPanelView로 직접 감싼 MenuView는 포커스를 유지하면서 단일선·일반 제목·hint 테두리를 사용합니다. 일반 패널의 포커스 표현은 유지합니다.
- Rust: MenuWidget/MenuBarWidget/MenuPopupWidget은 같은 표시 원칙을 따릅니다. 공개 focused 필드는 소스 호환을 위해 유지하며 메뉴의 별도 포커스 장식을 추가하지 않습니다.
- 12개 팔레트 × Unicode/ASCII에서 Go Show 이후 출력과 Rust TestBackend의 단일선·제목·선택 스타일·두 칸 문자 경계·입력 포커스 유무를 검사합니다.
- 실제 Go·Rust 한영 PTY에서 메뉴·하위/뒤로 이동·배경 키/붙여넣기 차단·원래 호출 위치 복귀·마우스·리사이즈·종료를 검사합니다. 한영 UI 이미지 10개도 갱신합니다.

최종 로컬 결과와 소스·이미지 해시는 [결과 JSON](menu-single-border-results.json)을 따릅니다. 커밋·게시·원격 CI·릴리스·CentOS 검증은 수행하지 않습니다. 0.3.0의 [이전 메뉴 검증](menu.md)과 구분합니다.
