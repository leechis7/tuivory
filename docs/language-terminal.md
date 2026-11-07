# 독립 언어의 입력·터미널 API

**한국어 (기본)** · [English](language-terminal.en.md)

Python·TypeScript/JavaScript·C·C++·Java는 공통 입력 이벤트와 선택적 터미널 세션을 각 언어로 구현한다. 기존 공개 import/include 하나로 사용한다. 모델·그리기에는 세션을 열 필요가 없다. TVR-15·16·30·31·32의 미배포 기능이며 공개 0.11.1에는 포함되지 않는다.

| 용도 | Python | TS/JS | C | C++ | Java |
| --- | --- | --- | --- | --- | --- |
| 입력 해석 | InputDecoder.feed/next | InputDecoder.feed/next | tui_input_decoder_new, tui_input_feed/next | InputDecoder.feed/next | InputDecoder.feed/next |
| 이벤트 | InputEvent | InputEvent | TuiInputEvent | InputEvent | InputEvent |
| 세션 | Terminal 컨텍스트 | Terminal.open/close | tui_terminal_new/open/close/free | Terminal.open/close, RAII | Terminal.open/close, AutoCloseable |
| 읽기 | read(초), 기본 0.1 | read(밀리초), 기본 100, Promise | tui_terminal_read(밀리초) | read(밀리초), 기본 100 | read(밀리초), 기본 100 |
| 크기·출력 | size, write | size, write | tui_terminal_size/write | size(), write | size(), write |

## 입력 해석

InputDecoder는 단말 없이 바이트를 복사·누적한다. Python/C/C++/Java는 바이트를, TS/JS는 Uint8Array 또는 문자열을 받는다. 완성된 이벤트를 next로 하나씩 꺼낸다. 다음 조각을 기다릴 때는 Python/TS/Java의 None/null, C++의 빈 optional, C의 TUI_OK와 NULL output을 반환한다. 불완전한 UTF-8을 먼저 문자로 내보내지 않는다. 잘못된 UTF-8은 대체 문자로 처리한다. 이벤트는 코드 포인트 단위이므로 결합 문자·ZWJ가 여러 이벤트로 들어올 수 있다. Text 모델이 원문의 그래핌을 관리한다.

이벤트 필드는 key, text, x, y, button이다. 좌표는 0부터 시작한다. mouse/mouse_move/mouse_release, wheel, text, paste, resize, eof와 키 이벤트를 구분한다. button에는 SGR의 버튼·수정 비트를 그대로 보관한다. resize의 x/y는 열/행이다. 앱이 좌표를 컴포넌트 내부 좌표로 변환하고 포인터 캡처를 라우팅한다.

방향키, Home/End, PageUp/PageDown, Delete, Tab/Shift+Tab, Enter, Backspace, F1/F2/F10/Shift+F10, ctrl_a 같은 제어 키를 해석한다. Escape 하나와 키 시퀀스의 시작을 구분하기 위해 세션은 약 100ms를 기다린다. 직접 해석기를 쓰는 앱은 next의 flush_escape/flushEscape 인자로 만료를 알린다. 모르는 완성 CSI는 unknown이다. 앱의 전역 키와 메뉴 내용은 정의하지 않는다.

Bracketed paste는 줄바꿈·탭·Escape를 리터럴 text 한 개로 반환한다. 붙여넣기 내용을 키 명령으로 실행하지 않는다. 원문은 최대 16MiB이며 초과 입력은 paste_rejected로 거부한다. 입력 버퍼도 제한한다. 마우스 좌표·버튼 수가 범위를 벗어나거나 형식이 잘못되면 unknown으로 거부한다. C의 text_length는 NUL이 들어간 붙여넣기도 표현하므로 해당 길이로 읽는다.

## 세션과 앱의 책임

Python의 Terminal(mouse_motion=True), TS의 new Terminal({mouseMotion:true}), C의 TuiTerminalOptions, C++의 TerminalOptions, Java의 new Terminal(true,true)로 버튼을 누른 이동 보고를 선택한다. 일반 마우스 보고는 기본 활성, 이동 보고는 기본 비활성이다. mouse=false는 마우스를 켜지 않는다.

세션은 raw 모드·대체 화면·bracketed paste·선택한 마우스 모드를 열고 close/컨텍스트 종료에서 복원한다. 읽기 제한 시간 동안 이벤트가 없으면 빈 값을 반환하며, 닫힌 세션은 eof를 반환한다. 제한 시간은 0~3600초 또는 0~3,600,000ms다. 원래의 파일 디스크립터·표준 스트림은 닫지 않는다. TS는 이전 raw 상태와 입력 스트림의 읽기 상태를 보존하고 자기 이벤트 리스너만 제거한다. 단말 하나에 활성 세션 하나와 reader 하나를 사용한다. C/C++/Python의 세션을 여러 스레드에서 동시에 호출하지 않는다.

앱은 세션의 수명, 화면 구성, 전역 키·포커스, 신호 처리와 종료 정책을 결정한다. 특히 C/C++/Python/Node 앱은 SIGTERM 처리에서 정상 종료 경로를 거쳐야 단말을 복원한다. 제공하는 실행 검증과 예제 호스트는 이 경로를 검사한다. Java 세션은 JVM shutdown hook으로 복원하며 정상 close에서는 hook을 해제한다. SIGKILL처럼 정리 코드를 실행할 수 없는 종료는 복원 대상이 아니다.

    import tuivory as ui
    with ui.Terminal(mouse_motion=True) as terminal:
        while True:
            event = terminal.read()
            if event is None:
                continue
            if event.key in ('ctrl_q', 'eof'):  # 앱이 정한 종료 키
                break
            # 앱이 이벤트를 컴포넌트에 연결하고 Canvas.ansi()를 출력한다.

TS는 try/finally에서 terminal.close(), C는 tui_input_event_free와 tui_terminal_free, C++는 RAII, Java는 try-with-resources를 사용한다. C의 세션·해석기·이벤트에는 각각 대응하는 free가 필요하다. C read/next의 output 이벤트는 호출자가 소유한다. 오류는 C의 TuiResult, C++ 예외, Java IOException/인자 오류로 전달한다. TS의 동시 read는 거부하고 close는 기다리는 read를 깨운다.

## 런타임과 검증

Python/C/C++의 세션은 선택적 POSIX TTY용이다. 지원하지 않는 OS에서는 세션 열기를 거부하며 모델·해석기 사용과 분리한다. Node TTY 세션은 구조적으로 정의한 TerminalIO를 받아 사용자 정의 스트림으로도 검사할 수 있다. 공개 타입 선언은 @types/node를 필수로 요구하지 않는다.

Java 세션은 일반 Java17 JAR에서 POSIX의 /dev/tty와 OS stty 유틸리티를 사용한다. JNI·공유 네이티브 라이브러리·다른 Tuivory 언어 구현은 사용하지 않는다. stty 호출은 최대 약 2초, 화면 크기 조회는 약 250ms 간격으로 제한한다. Java 통합 예제의 휴대용 줄 입력은 계속 제공하며 raw 세션 사용은 앱이 선택한다. 현재 실제 세션 검증 환경은 Linux다.

C/C++ 패키지와 실행파일은 정적 링크·ELF 조건을 유지한다. Python/npm/JAR는 지정된 런타임 예외를 따른다. CentOS 검증은 하지 않는다. 실제 설치·지원 버전은 [언어 지원](languages.md)과 각 언어 README에 명시한다.

공통 바이트 조각 사례 40개, UTF-8·키·마우스·리터럴 붙여넣기·잘못된 입력을 검사한다. 실제 PTY에서는 분할 한글·리사이즈·유휴 read·정상 종료·SIGTERM 후 원래 termios와 표시 모드를 확인한다. C/C++ 외부 SDK는 ASan/UBSan·정적 링크, Java 외부 JAR는 release17로 검사한다. C/C++ 통합 예제는 키 입력 없는 리사이즈와 불완전한 UTF-8 입력 중 SIGTERM도 검사한다. Python/Node는 부분 open 실패·읽기 취소·이전 상태와 리스너 복원도 검사한다. [검증 도구](../tools/check_language_terminal.py)와 [근거](evidence/)는 로컬·원격 CI·게시 상태를 구분한다.
