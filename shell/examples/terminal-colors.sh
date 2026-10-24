#!/bin/sh
# Read-only ANSI palette sample. Does not change TERM, palette or preferences.
printf 'TERM=%s COLORTERM=%s\n' "${TERM-<unset>}" "${COLORTERM-<unset>}"
if command -v tput >/dev/null 2>&1; then
    printf 'terminfo colors: '
    tput colors 2>/dev/null || printf 'unknown\n'
fi
printf '\nForeground: normal / bold (compare the two rows)\n'
for weight in 0 1; do
    i=0
    while [ "$i" -lt 8 ]; do
        printf '\033[%s;3%sm %s:%s Abc \033[0m' "$weight" "$i" "$weight" "$i"
        i=$((i + 1))
    done
    printf '\n'
done
printf '\nBasic background x foreground (same-color cells intentionally unreadable)\n'
bg=0
while [ "$bg" -lt 8 ]; do
    fg=0
    while [ "$fg" -lt 8 ]; do
        printf '\033[0;3%s;4%sm %s/%s \033[0m' "$fg" "$bg" "$fg" "$bg"
        fg=$((fg + 1))
    done
    printf '\n'
    bg=$((bg + 1))
done
printf '\033[0m\nNo terminal settings were changed.\n'
