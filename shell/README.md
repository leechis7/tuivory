# Tuivory Shell

현재는 [단말 색상 프로필](../docs/terminal-profiles.md)을 관찰하는 POSIX 셸 ANSI 색상 견본만 제공합니다. 공통 토큰을 적용하는 재사용 Shell 함수 패키지는 아직 구현하지 않았습니다. Go나 Python 런타임을 요구하지 않습니다.

```sh
sh shell/examples/terminal-colors.sh
```

이 예제는 ANSI 견본을 출력하며 단말 설정이나 사용자 팔레트를 변경하지 않습니다. 공통 디자인 데이터 해석과 UI 템플릿은 후속 작업입니다.
