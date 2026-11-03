package main

import (
	"crypto/sha256"
	"fmt"
	"go/ast"
	"go/build/constraint"
	"go/format"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// These are filename suffixes recognized by Go, including historical targets.
// Tags such as unix are expressions, not implicit filename constraints.
var gooses = strings.Fields("aix android darwin dragonfly freebsd hurd illumos ios js linux nacl netbsd openbsd plan9 solaris wasip1 windows zos")
var goarches = strings.Fields("386 amd64 amd64p32 arm armbe arm64 arm64be loong64 mips mipsle mips64 mips64le mips64p32 mips64p32le ppc ppc64 ppc64le riscv riscv64 s390 s390x sparc sparc64 wasm")

func contains(list []string, s string) bool {
	for _, v := range list {
		if v == s {
			return true
		}
	}
	return false
}

func andBuild(a, b string) string {
	if a == b {
		return a
	}
	if a == "" {
		return b
	}
	if b == "" {
		return a
	}
	e, err := constraint.Parse("//go:build (" + a + ") && (" + b + ")")
	must(err)
	return e.String()
}

func fileConstraint(name string, f *ast.File) string {
	var result string
	modern := false
	for _, group := range f.Comments {
		if group.Pos() > f.Package {
			break
		}
		for _, c := range group.List {
			if constraint.IsGoBuild(c.Text) {
				e, err := constraint.Parse(c.Text)
				must(err)
				result = e.String()
				modern = true
			}
		}
	}
	if !modern {
		for _, group := range f.Comments {
			if group.Pos() > f.Package {
				break
			}
			for _, c := range group.List {
				if constraint.IsPlusBuild(c.Text) {
					e, err := constraint.Parse(c.Text)
					must(err)
					result = andBuild(result, e.String())
				}
			}
		}
	}
	// Go applies filename constraints in addition to an explicit build line.
	stem, _, _ := strings.Cut(filepath.Base(name), ".")
	parts := strings.Split(stem, "_")
	if n := len(parts); n > 1 {
		last := parts[n-1]
		if contains(goarches, last) {
			result = andBuild(result, last)
			if n > 2 && contains(gooses, parts[n-2]) {
				result = andBuild(result, parts[n-2])
			}
		} else if contains(gooses, last) {
			result = andBuild(result, last)
		}
	}
	return result
}

// OR all implementations, e.g. Windows and !Windows stubs form a portable API.
// Evaluate independent build tags rather than assuming the generation host OS.
func unionBuild(conditions []string) string {
	unique := map[string]bool{}
	for _, c := range conditions {
		if c == "" {
			return ""
		}
		unique[c] = true
	}
	var sorted []string
	for c := range unique {
		sorted = append(sorted, "("+c+")")
	}
	sort.Strings(sorted)
	e, err := constraint.Parse("//go:build " + strings.Join(sorted, " || "))
	must(err)
	tags := map[string]bool{}
	// Collect structurally because expression evaluation can short-circuit.
	var collect func(constraint.Expr)
	collect = func(e constraint.Expr) {
		switch e := e.(type) {
		case *constraint.TagExpr:
			tags[e.Tag] = true
		case *constraint.NotExpr:
			collect(e.X)
		case *constraint.AndExpr:
			collect(e.X)
			collect(e.Y)
		case *constraint.OrExpr:
			collect(e.X)
			collect(e.Y)
		}
	}
	collect(e)
	var names []string
	for name := range tags {
		names = append(names, name)
	}
	sort.Strings(names)
	if len(names) <= 16 {
		always := true
		for mask := 0; mask < 1<<len(names); mask++ {
			if !e.Eval(func(tag string) bool { return mask&(1<<sort.SearchStrings(names, tag)) != 0 }) {
				always = false
				break
			}
		}
		if always {
			return ""
		}
	}
	return e.String()
}

func declaredNames(f *ast.File) []string {
	var names []string
	for _, d := range f.Decls {
		switch d := d.(type) {
		case *ast.FuncDecl:
			if d.Recv == nil && d.Name.IsExported() {
				names = append(names, d.Name.Name)
			}
		case *ast.GenDecl:
			for _, s := range d.Specs {
				switch s := s.(type) {
				case *ast.TypeSpec:
					if s.Name.IsExported() {
						names = append(names, s.Name.Name)
					}
				case *ast.ValueSpec:
					for _, n := range s.Names {
						if n.IsExported() {
							names = append(names, n.Name)
						}
					}
				}
			}
		}
	}
	return names
}

func backendConstraints(dir string, files []string) map[string]string {
	conditions := map[string][]string{}
	seen := map[string]bool{}
	for _, name := range files {
		if seen[name] || strings.HasSuffix(name, "_test.go") {
			continue
		}
		seen[name] = true
		f, err := parser.ParseFile(token.NewFileSet(), filepath.Join(dir, name), nil, parser.ParseComments)
		must(err)
		c := fileConstraint(name, f)
		for _, name := range declaredNames(f) {
			conditions[name] = append(conditions[name], c)
		}
	}
	result := map[string]string{}
	for name, cs := range conditions {
		result[name] = unionBuild(cs)
	}
	return result
}

func generatedFile(pkg, build string, imports map[string]string, declarations []string) []byte {
	body := strings.Join(declarations, "\n")
	f, err := parser.ParseFile(token.NewFileSet(), "generated.go", "package "+pkg+"\n"+body, 0)
	must(err)
	used := map[string]bool{}
	ast.Inspect(f, func(n ast.Node) bool {
		if s, ok := n.(*ast.SelectorExpr); ok {
			if id, ok := s.X.(*ast.Ident); ok {
				used[id.Name] = true
			}
		}
		return true
	})
	var out strings.Builder
	out.WriteString("// Code generated by go run ./internal/cmd/facadegen; DO NOT EDIT.\n")
	if build != "" {
		fmt.Fprintf(&out, "//go:build %s\n", build)
	}
	fmt.Fprintf(&out, "\npackage %s\n\n", pkg)
	var names []string
	for name := range imports {
		if used[name] {
			names = append(names, name)
		}
	}
	sort.Strings(names)
	if len(names) > 0 {
		out.WriteString("import (\n")
		for _, name := range names {
			fmt.Fprintf(&out, "%s %q\n", name, imports[name])
		}
		out.WriteString(")\n\n")
	}
	out.WriteString(body)
	formatted, err := format.Source([]byte(out.String()))
	must(err)
	return formatted
}

func writePlatformFiles(dir, prefix, pkg string, imports map[string]string, groups map[string][]string, check bool) {
	expected := map[string]bool{}
	for condition, decls := range groups {
		name := prefix + "_generated.go"
		if condition != "" {
			digest := sha256.Sum256([]byte(condition))
			name = fmt.Sprintf("%s_platform_%x_generated.go", prefix, digest[:6])
		}
		file := filepath.Join(dir, name)
		expected[file] = true
		write(file, generatedFile(pkg, condition, imports, decls), check)
	}
	files, err := filepath.Glob(filepath.Join(dir, prefix+"_platform_*_generated.go"))
	must(err)
	for _, file := range files {
		if !expected[file] {
			if check {
				panic("stale facade: " + file)
			}
			must(os.Remove(file))
		}
	}
}
