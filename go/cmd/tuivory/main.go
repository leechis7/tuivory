// TUIVORY is a DB-free, interactive component and theme playground.
package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/leechis7/tuivory/go/internal/playground"
)

func main() {
	theme := flag.String("theme", "dark", "dark, light, blackwhite")
	colors := flag.String("colors", "auto", "auto, 8, 16, 256, truecolor (preview; terminal capability is unchanged)")
	mouse := flag.Bool("mouse", true, "enable mouse interaction")
	lang := flag.String("lang", "ko", "UI language: ko, en (default: Korean)")
	flag.Parse()
	if os.Getenv("TERM") == "" {
		_ = os.Setenv("TERM", "ansi")
	}
	if err := playground.Run(playground.Options{Theme: *theme, Colors: *colors, Mouse: *mouse, Lang: *lang}); err != nil {
		fmt.Fprintln(os.Stderr, "TUIVORY:", err)
		os.Exit(1)
	}
}
