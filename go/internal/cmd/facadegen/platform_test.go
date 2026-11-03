package main

import (
	"go/build"
	"go/build/constraint"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func enabled(t *testing.T, c string, tags ...string) bool {
	t.Helper()
	if c == "" {
		return true
	}
	e, err := constraint.Parse("//go:build " + c)
	if err != nil {
		t.Fatal(err)
	}
	return e.Eval(func(tag string) bool { return contains(tags, tag) })
}

func TestBackendAvailabilityAndRootPropagation(t *testing.T) {
	dir := t.TempDir()
	files := map[string]string{
		"common.go":              "package fake\nfunc Common() {}\n",
		"tty_unix.go":            "//go:build linux || darwin\n\npackage fake\nfunc StdIO() {}\n",
		"tty_plan9.go":           "//go:build plan9\n\npackage fake\nfunc StdIO() {}\n",
		"console_windows.go":     "//go:build windows\n\npackage fake\nfunc Console() {}\n",
		"console_other.go":       "//go:build !windows\n\npackage fake\nfunc Console() {}\n",
		"feature_linux_amd64.go": "//go:build !minimal\n\npackage fake\nfunc Limited() {}\n",
		"legacy.go":              "// +build darwin\n\npackage fake\nfunc Legacy() {}\n",
		"ignored_test.go":        "package fake\nfunc TestOnly() {}\n",
	}
	var names []string
	for name, source := range files {
		if err := os.WriteFile(filepath.Join(dir, name), []byte(source), 0600); err != nil {
			t.Fatal(err)
		}
		names = append(names, name)
	}
	got := backendConstraints(dir, names)
	if got["Common"] != "" || got["Console"] != "" {
		t.Fatal("portable implementations were restricted", got)
	}
	if _, ok := got["TestOnly"]; ok {
		t.Fatal("test declaration exported")
	}
	for _, os := range []string{"linux", "darwin", "plan9"} {
		if !enabled(t, got["StdIO"], os) {
			t.Fatal("missing stdio platform", os)
		}
	}
	if enabled(t, got["StdIO"], "windows") {
		t.Fatal("Windows references Unix/Plan9 API")
	}
	if !enabled(t, got["Limited"], "linux", "amd64") || enabled(t, got["Limited"], "linux", "arm64") || enabled(t, got["Limited"], "linux", "amd64", "minimal") {
		t.Fatal("filename or explicit constraints lost", got)
	}
	if !enabled(t, got["Legacy"], "darwin") || enabled(t, got["Legacy"], "windows") {
		t.Fatal("legacy build line lost")
	}
	// The second generation stage reads the emitted SDK's constraints, not just
	// its exported names, and drops unused imports from platform files.
	generated := generatedFile("terminal", got["StdIO"], map[string]string{"native": "example.com/backend", "unused": "time"}, []string{"func StdIO() { native.StdIO() }"})
	if strings.Contains(string(generated), "\"time\"") {
		t.Fatal("unused platform import")
	}
	sdk := filepath.Join(dir, "sdk")
	if err := os.Mkdir(sdk, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(sdk, "compat_generated.go"), generated, 0600); err != nil {
		t.Fatal(err)
	}
	decls := packageDecls(sdk)
	if len(decls) != 1 || enabled(t, decls[0].build, "windows") || !enabled(t, decls[0].build, "plan9") {
		t.Fatal("root lost platform availability", decls)
	}
}

func TestFilenameConstraintsMatchGoBuild(t *testing.T) {
	dir := t.TempDir()
	for _, name := range []string{"api.go", "api_windows.go", "api_linux_amd64.go", "api_linux.extra.go", "api_unix.go"} {
		if err := os.WriteFile(filepath.Join(dir, name), []byte("package fixture\n"), 0600); err != nil {
			t.Fatal(err)
		}
		f, err := parser.ParseFile(token.NewFileSet(), name, "package fixture\n", parser.ParseComments)
		if err != nil {
			t.Fatal(err)
		}
		condition := fileConstraint(name, f)
		for _, target := range [][2]string{{"windows", "amd64"}, {"linux", "amd64"}, {"linux", "arm64"}, {"darwin", "arm64"}} {
			ctx := build.Default
			ctx.GOOS = target[0]
			ctx.GOARCH = target[1]
			want, err := ctx.MatchFile(dir, name)
			if err != nil {
				t.Fatal(err)
			}
			if got := enabled(t, condition, target[:]...); got != want {
				t.Fatal(name, target, condition, got, want)
			}
		}
	}
}

func TestPlatformOutputRefreshRemovesObsoleteGeneratedFiles(t *testing.T) {
	dir := t.TempDir()
	imports := map[string]string{"native": "example.com/backend"}
	writePlatformFiles(dir, "compat", "terminal", imports, map[string][]string{"windows": {"func Platform() { native.Platform() }"}}, false)
	old, _ := filepath.Glob(filepath.Join(dir, "compat_platform_*_generated.go"))
	if len(old) != 1 {
		t.Fatal(old)
	}
	manual := filepath.Join(dir, "host.go")
	if err := os.WriteFile(manual, []byte("package terminal\n"), 0600); err != nil {
		t.Fatal(err)
	}
	groups := map[string][]string{"linux": {"func Platform() { native.Platform() }"}}
	writePlatformFiles(dir, "compat", "terminal", imports, groups, false)
	if _, err := os.Stat(old[0]); !os.IsNotExist(err) {
		t.Fatal("stale platform file remains", err)
	}
	if _, err := os.Stat(manual); err != nil {
		t.Fatal("host file removed", err)
	}
	writePlatformFiles(dir, "compat", "terminal", imports, groups, true)
}

func TestCheckAcceptsWindowsCheckoutLineEndings(t *testing.T) {
	file := filepath.Join(t.TempDir(), "generated.go")
	canonical := []byte("package fixture\n\nfunc Ready() {}\n")
	checkout := strings.ReplaceAll(string(canonical), "\n", "\r\n")
	if err := os.WriteFile(file, []byte(checkout), 0600); err != nil {
		t.Fatal(err)
	}
	write(file, canonical, true)
}
