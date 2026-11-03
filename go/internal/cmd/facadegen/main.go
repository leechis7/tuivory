// facadegen generates SDK-owned compatibility declarations from pinned modules.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/printer"
	"go/token"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type module struct {
	Dir, Name, ImportPath string
	GoFiles               []string
	IgnoredGoFiles        []string
	CgoFiles              []string
	Module                struct{ Version string }
}
type entry struct {
	Name            string   `json:"name"`
	Kind            string   `json:"kind"`
	Target          string   `json:"target"`
	SDK             []string `json:"sdk"`
	BuildConstraint string   `json:"build_constraint,omitempty"`
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func printed(n any) string {
	var b bytes.Buffer
	must(printer.Fprint(&b, token.NewFileSet(), n))
	return b.String()
}
func main() {
	check := flag.Bool("check", false, "verify generated files")
	flag.Parse()
	manifest := map[string]any{"format": 1, "scope": "Pinned SDK compatibility; aliases retain backend identity except the responsive Modal adapter, which embeds its backend. Global setters are explicit; no consumer-local shim.", "packages": map[string]any{}}
	for _, cfg := range []struct{ source, out, name string }{{"github.com/rivo/tview", "ui", "ui"}, {"github.com/gdamore/tcell/v2", "terminal", "terminal"}} {
		// Keep the established inventory stable on every generation host. Inspect
		// all implementations below to derive each exported API's availability.
		command := exec.Command("go", "list", "-json", cfg.source)
		command.Env = append(os.Environ(), "GOOS=linux", "GOARCH=amd64", "CGO_ENABLED=0")
		raw, err := command.Output()
		must(err)
		var m module
		must(json.Unmarshal(raw, &m))
		availability := backendConstraints(m.Dir, append(append(append([]string{}, m.GoFiles...), m.IgnoredGoFiles...), m.CgoFiles...))
		imports := map[string]string{"native": cfg.source}
		decls := map[string]string{}
		entries := []entry{}
		for _, file := range m.GoFiles {
			f, err := parser.ParseFile(token.NewFileSet(), filepath.Join(m.Dir, file), nil, 0)
			must(err)
			fileImports := map[string]string{}
			for _, i := range f.Imports {
				p, _ := strconv.Unquote(i.Path.Value)
				name := path.Base(p)
				if strings.HasPrefix(name, "v") && len(name) > 1 && name[1] >= '0' && name[1] <= '9' {
					name = path.Base(path.Dir(p))
				}
				if i.Name != nil {
					name = i.Name.Name
				}
				fileImports[name] = p
			}
			useImports := func(node ast.Node) {
				ast.Inspect(node, func(n ast.Node) bool {
					if s, ok := n.(*ast.SelectorExpr); ok {
						if id, ok := s.X.(*ast.Ident); ok {
							if p, ok := fileImports[id.Name]; ok {
								if p == "github.com/gdamore/tcell/v2" && cfg.name == "ui" {
									p = "github.com/leechis7/tuivory/go/terminal"
								}
								if prev, ok := imports[id.Name]; ok && prev != p {
									panic("import collision")
								}
								imports[id.Name] = p
							}
						}
					}
					return true
				})
			}
			for _, d := range f.Decls {
				if fn, ok := d.(*ast.FuncDecl); ok {
					if fn.Recv != nil || !fn.Name.IsExported() {
						continue
					}
					name := fn.Name.Name
					args := []string{}
					n := 0
					if fn.Type.TypeParams != nil {
						panic("review generic forwarder")
					}
					for _, p := range fn.Type.Params.List {
						if len(p.Names) == 0 {
							p.Names = []*ast.Ident{ast.NewIdent(fmt.Sprintf("arg%d", n))}
						}
						for _, id := range p.Names {
							if id.Name == "_" {
								id.Name = fmt.Sprintf("arg%d", n)
							}
							args = append(args, id.Name)
							n++
						}
					}
					if len(fn.Type.Params.List) > 0 {
						if _, ok := fn.Type.Params.List[len(fn.Type.Params.List)-1].Type.(*ast.Ellipsis); ok {
							args[len(args)-1] += "..."
						}
					}
					useImports(fn.Type)
					sig := strings.TrimPrefix(printed(fn.Type), "func")
					call := "native." + name + "(" + strings.Join(args, ",") + ")"
					if fn.Type.Results != nil && len(fn.Type.Results.List) > 0 {
						call = "return " + call
					}
					decls[name] = "// " + name + " forwards to the pinned backend without changing behavior.\nfunc " + name + sig + " { " + call + " }\n"
					entries = append(entries, entry{Name: name, Kind: "function", Target: cfg.source + "." + name})
					continue
				}
				gen, ok := d.(*ast.GenDecl)
				if !ok {
					continue
				}
				for _, spec := range gen.Specs {
					switch s := spec.(type) {
					case *ast.TypeSpec:
						if !s.Name.IsExported() {
							continue
						}
						name := s.Name.Name
						decls[name] = "type " + name + " = native." + name + "\n"
						entries = append(entries, entry{Name: name, Kind: "type", Target: cfg.source + "." + name})
					case *ast.ValueSpec:
						for _, id := range s.Names {
							if !id.IsExported() {
								continue
							}
							name := id.Name
							if cfg.name == "ui" && gen.Tok == token.VAR {
								switch name {
								case "Borders":
									borderType := s.Type
									if borderType == nil {
										borderType = s.Values[0].(*ast.CompositeLit).Type
									}
									useImports(borderType)
									decls[name] = "// Borders is a startup snapshot. Use GetBorders/SetBorders for global updates.\nvar Borders = native.Borders\ntype BorderSymbols = " + printed(borderType) + "\nfunc GetBorders() BorderSymbols { return native.Borders }\nfunc SetBorders(value BorderSymbols) { native.Borders = value }\n"
								case "Styles":
									decls[name] = "// Styles is a startup snapshot. Use GetStyles/SetStyles for global updates.\nvar Styles = native.Styles\nfunc GetStyles() Theme { return native.Styles }\nfunc SetStyles(value Theme) { native.Styles = value }\n"
								case "DoubleClickInterval":
									imports["time"] = "time"
									decls[name] = "func GetDoubleClickInterval() time.Duration { return native.DoubleClickInterval }\nfunc SetDoubleClickInterval(value time.Duration) { native.DoubleClickInterval = value }\n"
								case "NewLine":
									decls[name] = "func GetNewLine() string { return native.NewLine }\nfunc SetNewLine(value string) { native.NewLine = value }\n"
								case "DefaultFormFieldWidth", "DefaultFormFieldHeight", "TabSize":
									decls[name] = "func Get" + name + "() int { return native." + name + " }\nfunc Set" + name + "(value int) { native." + name + " = value }\n"
								case "SemigraphicJoints":
									decls[name] = "var SemigraphicJoints = native.SemigraphicJoints\nfunc SetSemigraphicJoints(value map[string]rune) { native.SemigraphicJoints = value; SemigraphicJoints = value }\n"
								case "InputFieldInteger", "InputFieldFloat", "InputFieldMaxLength":
									decls[name] = "var " + name + " = native." + name + "\n"
								default:
									panic("review mutable global " + name)
								}
							} else {
								kind := gen.Tok.String()
								decls[name] = kind + " " + name + " = native." + name + "\n"
							}
							entries = append(entries, entry{Name: name, Kind: gen.Tok.String(), Target: cfg.source + "." + name})
						}
					}
				}
			}
		}
		if cfg.name == "ui" {
			imports["widgets"] = "github.com/leechis7/tuivory/go/internal/widgets"
			decls["Modal"] = "// Modal is the SDK responsive adapter and embeds the pinned backend Modal.\ntype Modal = widgets.Modal\n"
			decls["NewModal"] = "// NewModal creates a responsive message window with wrapping buttons.\nfunc NewModal() *Modal { return widgets.NewModal() }\n"
		}
		names := []string{}
		for name := range decls {
			names = append(names, name)
		}
		sort.Strings(names)
		groups := map[string][]string{}
		for _, name := range names {
			condition := availability[name]
			groups[condition] = append(groups[condition], decls[name])
		}
		writePlatformFiles(cfg.out, "compat", cfg.name, imports, groups, *check)
		for i := range entries {
			e := &entries[i]
			e.BuildConstraint = availability[e.Name]
			prefix := "github.com/leechis7/tuivory/go/" + cfg.name + "."
			e.SDK = []string{prefix + e.Name}
			if cfg.name == "ui" && e.Kind == "var" {
				switch e.Name {
				case "Borders", "Styles":
					e.SDK = append(e.SDK, prefix+"Get"+e.Name, prefix+"Set"+e.Name)
				case "DoubleClickInterval", "NewLine", "DefaultFormFieldWidth", "DefaultFormFieldHeight", "TabSize":
					e.SDK = []string{prefix + "Get" + e.Name, prefix + "Set" + e.Name}
				case "SemigraphicJoints":
					e.SDK = append(e.SDK, prefix+"Set"+e.Name)
				}
			}
		}
		sort.Slice(entries, func(i, j int) bool { return entries[i].Name < entries[j].Name })
		manifest["packages"].(map[string]any)["github.com/leechis7/tuivory/go/"+cfg.name] = map[string]any{"backend": cfg.source, "version": m.Module.Version, "symbols": entries}
	}
	root := generateRoot(*check)
	manifest["root"] = root
	for _, pkg := range manifest["packages"].(map[string]any) {
		entries := pkg.(map[string]any)["symbols"].([]entry)
		for i := range entries {
			for _, name := range append([]string(nil), entries[i].SDK...) {
				if name, ok := root[name]; ok {
					entries[i].SDK = append(entries[i].SDK, name)
				}
			}
		}
	}
	data, err := json.MarshalIndent(manifest, "", "  ")
	must(err)
	write("../design/go-facade-symbols.json", append(data, '\n'), *check)
}
func write(p string, data []byte, check bool) {
	if check {
		old, err := os.ReadFile(p)
		must(err)
		// Git may check out generated text with CRLF on Windows. Compare the
		// canonical line endings while still detecting declaration changes.
		if !bytes.Equal(bytes.ReplaceAll(old, []byte("\r\n"), []byte("\n")), data) {
			panic("stale facade: " + p)
		}
		return
	}
	must(os.MkdirAll(filepath.Dir(p), 0755))
	must(os.WriteFile(p, data, 0644))
}
