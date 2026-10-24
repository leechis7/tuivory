// Package tokens loads TUIVORY's language-neutral draft tokens without a UI framework.
package tokens

import (
	"encoding/json"
	"fmt"
	"io"
	"regexp"
	"strconv"
	"strings"
)

const Format = "tuivory.tokens.draft"

// Pair keeps terminal indices separate from their reference RGB values.
type Pair struct {
	Foreground          string `json:"foreground"`
	Background          string `json:"background"`
	ReferenceForeground string `json:"referenceForeground"`
	ReferenceBackground string `json:"referenceBackground"`
	FontWeight          string `json:"fontWeight"`
}

type Palette map[string]Pair

type Document struct {
	Format   string             `json:"format"`
	Roles    []string           `json:"roles"`
	Palettes map[string]Palette `json:"palettes"`
}

var rgb = regexp.MustCompile(`^#[0-9a-fA-F]{6}$`)
var index = regexp.MustCompile(`^(0|[1-9][0-9]{0,2})$`)

// Parse validates a complete document. It performs no terminal or filesystem I/O.
func Parse(data []byte) (*Document, error) {
	var d Document
	decoder := json.NewDecoder(strings.NewReader(string(data)))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&d); err != nil {
		return nil, err
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return nil, fmt.Errorf("unexpected content after token document")
	}
	if d.Format != Format || len(d.Roles) == 0 || len(d.Palettes) == 0 {
		return nil, fmt.Errorf("invalid token format or empty document")
	}
	seen := map[string]bool{}
	for _, role := range d.Roles {
		if role == "" || seen[role] {
			return nil, fmt.Errorf("empty/duplicate role: %q", role)
		}
		seen[role] = true
	}
	for name, palette := range d.Palettes {
		parts := strings.Split(name, "-")
		if len(parts) != 2 || (parts[0] != "dark" && parts[0] != "light" && parts[0] != "blackwhite") {
			return nil, fmt.Errorf("invalid palette: %s", name)
		}
		limit := 0
		switch parts[1] {
		case "8":
			limit = 8
		case "16":
			limit = 16
		case "256":
			limit = 256
		case "truecolor":
			limit = 256
		default:
			return nil, fmt.Errorf("invalid profile: %s", name)
		}
		if len(palette) != len(d.Roles) {
			return nil, fmt.Errorf("incomplete palette: %s", name)
		}
		for role, pair := range palette {
			if !seen[role] {
				return nil, fmt.Errorf("unknown role: %s", role)
			}
			for _, color := range []string{pair.Foreground, pair.Background} {
				if strings.HasPrefix(color, "#") {
					if parts[1] != "truecolor" || !rgb.MatchString(color) {
						return nil, fmt.Errorf("invalid RGB in %s: %s", name, color)
					}
				} else {
					n, err := strconv.Atoi(color)
					if err != nil || !index.MatchString(color) || n >= limit {
						return nil, fmt.Errorf("invalid index in %s: %s", name, color)
					}
				}
			}
			if !rgb.MatchString(pair.ReferenceForeground) || !rgb.MatchString(pair.ReferenceBackground) || (pair.FontWeight != "none" && pair.FontWeight != "bold") {
				return nil, fmt.Errorf("invalid reference/weight: %s/%s", name, role)
			}
		}
	}
	return &d, nil
}

// Candidate returns a fresh document so one caller cannot mutate another's theme.
func Candidate() (*Document, error) { return Parse([]byte(CandidateJSON())) }

// Palette resolves an explicit theme/profile pair. Detection belongs to the host.
func (d *Document) Palette(theme, profile string) (Palette, error) {
	p, ok := d.Palettes[theme+"-"+profile]
	if !ok {
		return nil, fmt.Errorf("unknown palette: %s-%s", theme, profile)
	}
	copy := Palette{}
	for role, pair := range p {
		copy[role] = pair
	}
	return copy, nil
}
