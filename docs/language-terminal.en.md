# Input and terminal APIs in independent language ports

[한국어 (기본)](language-terminal.md) · **English**

Python, TypeScript/JavaScript, C, C++ and Java independently implement common input events and optional terminal sessions through the existing single public import/include. Models/rendering do not require an open session. This unreleased TVR-15/16/30/31/32 work is absent from public 0.11.1.

| Purpose | Python | TS/JS | C | C++ | Java |
| --- | --- | --- | --- | --- | --- |
| Decoder | InputDecoder.feed/next | InputDecoder.feed/next | tui_input_decoder_new, tui_input_feed/next | InputDecoder.feed/next | InputDecoder.feed/next |
| Event | InputEvent | InputEvent | TuiInputEvent | InputEvent | InputEvent |
| Session | Terminal context | Terminal.open/close | tui_terminal_new/open/close/free | Terminal.open/close, RAII | Terminal.open/close, AutoCloseable |
| Read | read(seconds), default .1 | read(milliseconds), default 100, Promise | tui_terminal_read(milliseconds) | read(milliseconds), default 100 | read(milliseconds), default 100 |
| Size/output | size, write | size, write | tui_terminal_size/write | size(), write | size(), write |

## Decoding input

InputDecoder copies/increments bytes without accessing a terminal. Python/C/C++/Java accept bytes; TS/JS accepts Uint8Array or strings. Call next for each completed event. Pending fragments return None/null, an empty C++ optional, or C TUI_OK with NULL output. Incomplete UTF-8 does not become a character prematurely. Invalid UTF-8 uses replacement characters. Events contain individual code points: combining marks/ZWJ may arrive separately, while Text maintains source graphemes.

Events have key, text, x, y and button. Coordinates are zero-based. They distinguish mouse/mouse_move/mouse_release, wheel, text, paste, resize, eof and keys. Button retains SGR button/modifier bits. Resize x/y means columns/rows. Hosts translate component-local coordinates and route capture.

Supported keys include arrows, Home/End, PageUp/PageDown, Delete, Tab/Shift+Tab, Enter, Backspace, F1/F2/F10/Shift+F10 and control keys such as ctrl_a. Sessions wait approximately 100ms to distinguish Escape from a sequence prefix. Direct decoder users pass flush_escape/flushEscape to next after their own deadline. Unknown completed CSI produces unknown. Global keys/menu contents belong to hosts.

Bracketed paste produces one literal text payload, preserving newlines, tabs and Escape. It never executes pasted keys. Source paste is limited to 16MiB; oversized input produces paste_rejected. Input buffering is also bounded. Malformed/out-of-range mouse coordinates/buttons produce unknown. C text_length represents pasted NUL bytes, so read that length.

## Session lifecycle and host responsibilities

Select button-motion reporting with Python Terminal(mouse_motion=True), TS new Terminal({mouseMotion:true}), C TuiTerminalOptions, C++ TerminalOptions or Java new Terminal(true,true). Regular mouse reporting defaults on; motion defaults off. Mouse=false leaves reporting off.

Sessions enable raw mode, the alternate screen, bracketed paste and selected mouse modes, restoring them on close/context exit. Read returns an empty value on timeout and eof after close. Timeouts range from 0–3600 seconds or 0–3,600,000ms. Borrowed file descriptors/standard streams are never closed. TS preserves previous raw/input-reading state and removes only its own listeners. Use one active session and one reader per terminal. Do not call C/C++/Python sessions concurrently from multiple threads.

Hosts decide lifecycle, composition, global keys/focus, signals and exit policy. C/C++/Python/Node hosts must route SIGTERM through cleanup to restore the terminal; supplied execution checks/example hosts verify this. Java restores through a JVM shutdown hook and removes the hook on normal close. Termination such as SIGKILL cannot run cleanup.

    import tuivory as ui
    with ui.Terminal(mouse_motion=True) as terminal:
        while True:
            event = terminal.read()
            if event is None:
                continue
            if event.key in ('ctrl_q', 'eof'):  # Host-selected quit key
                break
            # Route events to components and write Canvas.ansi() in the host.

Use TS try/finally with terminal.close(), C tui_input_event_free/tui_terminal_free, C++ RAII or Java try-with-resources. C session/decoder/event handles have matching free functions. C read/next output events belong to the caller. Errors use C TuiResult, C++ exceptions and Java IOException/argument errors. TS rejects simultaneous reads and close wakes a pending read.

## Runtimes and validation

Python/C/C++ sessions are optional POSIX TTY adapters. Unsupported operating systems reject session opening independently of models/decoders. Node accepts structurally defined TerminalIO for custom stream tests. Public declarations do not require @types/node.

Java uses POSIX /dev/tty and the OS stty utility from a normal Java17 JAR, without JNI, shared native libraries or another Tuivory implementation. Stty calls are limited to approximately two seconds; size queries are throttled to approximately 250ms. The integrated Java example retains portable line input, while applications opt into raw sessions. Actual session validation currently runs on Linux.

C/C++ packages/examples retain static-link/ELF requirements. Python/npm/JAR follow their specified runtime exceptions. No CentOS validation runs. See [language support](languages.en.md) and language READMEs for installation/supported versions.

Validation covers 40 shared fragment cases for UTF-8, keys, mouse, literal paste and invalid input. Actual PTYs verify fragmented Korean, resize, bounded idle reads, normal close and SIGTERM with exact termios/display-mode restoration. External C/C++ SDK consumers use ASan/UBSan and static linking; external Java JAR consumers compile for release17. Native catalogs also verify resize without a key and SIGTERM during partial UTF-8 input. Python/Node test partial-open cleanup, read cancellation and previous state/listener restoration. [The checker](../tools/check_language_terminal.py) and [evidence](evidence/) distinguish local checks, remote CI and publication.
