// Package showcase runs all interactive examples in one executable.
package showcase

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/leechis7/tuivory/go/internal/playground"
	"github.com/leechis7/tuivory/go/internal/showcase/catalog"
	"github.com/leechis7/tuivory/go/internal/showcase/controls"
	"github.com/leechis7/tuivory/go/internal/showcase/focus"
	"github.com/leechis7/tuivory/go/internal/showcase/menu"
	"github.com/leechis7/tuivory/go/internal/showcase/syntax"
	"github.com/leechis7/tuivory/go/internal/showcase/tree"
	"github.com/leechis7/tuivory/go/internal/showcase/workspace"
)

const demos = "playground, tree, workspace, focus, catalog, menu, controls, syntax"

// Run consumes only the demo selector; all other arguments reach the example.
func Run(args []string) error {
	demo := "playground"
	var forwarded []string
	list, help, en, selected := false, false, false, false
	for i := 0; i < len(args); i++ {
		switch {
		case args[i] == "--demo":
			if selected || i+1 == len(args) {
				return fmt.Errorf("--demo requires one example: %s", demos)
			}
			i++
			demo = args[i]
			selected = true
		case strings.HasPrefix(args[i], "--demo="):
			if selected {
				return fmt.Errorf("--demo must occur once")
			}
			demo = strings.TrimPrefix(args[i], "--demo=")
			selected = true
		case args[i] == "--list":
			list = true
		default:
			forwarded = append(forwarded, args[i])
			if args[i] == "--help" || args[i] == "-h" {
				help = true
			}
			if args[i] == "--lang=en" || args[i] == "--lang" && i+1 < len(args) && args[i+1] == "en" {
				en = true
			}
		}
	}
	if list || help && !selected {
		if en {
			fmt.Println("Tuivory examples — one executable\n--demo NAME [example options]   --list\nDefault: playground\nExamples:", demos)
		} else {
			fmt.Println("Tuivory 예제 — 단일 실행파일\n--demo 이름 [예제 옵션]   --list\n기본: playground\n예제:", demos)
		}
		fmt.Println("--demo tree --lang ko\n--demo syntax --lang en\n--demo catalog --mode grid\n--demo NAME --help")
		return nil
	}
	if os.Getenv("TERM") == "" {
		_ = os.Setenv("TERM", "ansi")
	}
	switch demo {
	case "tree":
		tree.Run(forwarded)
	case "workspace":
		workspace.Run(forwarded)
	case "focus":
		focus.Run(forwarded)
	case "catalog":
		catalog.Run(forwarded)
	case "menu":
		menu.Run(forwarded)
	case "controls":
		controls.Run(forwarded)
	case "syntax":
		syntax.Run(forwarded)
	case "playground":
		flags := flag.NewFlagSet("playground", flag.ContinueOnError)
		theme := flags.String("theme", "dark", "dark, light, blackwhite")
		colors := flags.String("colors", "auto", "auto, 8, 16, 256, truecolor")
		mouse := flags.Bool("mouse", true, "enable mouse interaction")
		lang := flags.String("lang", "ko", "ko/en")
		if err := flags.Parse(forwarded); err != nil {
			if err == flag.ErrHelp {
				return nil
			}
			return err
		}
		return playground.Run(playground.Options{Theme: *theme, Colors: *colors, Mouse: *mouse, Lang: *lang})
	default:
		return fmt.Errorf("unknown demo %q; choose %s", demo, demos)
	}
	return nil
}
