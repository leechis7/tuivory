package tokens

import (
	"encoding/json"
	"testing"
)

func TestCandidateAndIsolation(t *testing.T) {
	d, err := Candidate()
	if err != nil {
		t.Fatal(err)
	}
	if len(d.Palettes) != 12 || len(d.Roles) != 16 {
		t.Fatal("missing reference palettes/roles")
	}
	p, err := d.Palette("dark", "8")
	if err != nil {
		t.Fatal(err)
	}
	delete(p, "body")
	if len(d.Palettes["dark-8"]) != 16 {
		t.Fatal("caller mutated shared palette")
	}
	delete(d.Palettes, "dark-8")
	next, err := Candidate()
	if err != nil || len(next.Palettes) != 12 {
		t.Fatal("candidate data leaked between callers")
	}
	if _, err := next.Palette("dark", "auto"); err == nil {
		t.Fatal("host detection must resolve auto")
	}
}

func TestRejectInvalidContracts(t *testing.T) {
	for _, name := range []string{"format", "duplicate", "missing", "extra", "index", "rgb", "weight", "profile"} {
		t.Run(name, func(t *testing.T) {
			d, err := Candidate()
			if err != nil {
				t.Fatal(err)
			}
			pair := d.Palettes["dark-8"]["body"]
			switch name {
			case "format":
				d.Format = "unknown"
			case "duplicate":
				d.Roles[1] = d.Roles[0]
			case "missing":
				delete(d.Palettes["dark-8"], "body")
			case "extra":
				d.Palettes["dark-8"]["unknown"] = pair
			case "index":
				pair.Foreground = "8"
				d.Palettes["dark-8"]["body"] = pair
			case "rgb":
				pair = d.Palettes["dark-truecolor"]["body"]
				pair.Background = "#zzzzzz"
				d.Palettes["dark-truecolor"]["body"] = pair
			case "weight":
				pair.FontWeight = "heavy"
				d.Palettes["dark-8"]["body"] = pair
			case "profile":
				d.Palettes["dark-auto"] = d.Palettes["dark-8"]
			}
			data, err := json.Marshal(d)
			if err != nil {
				t.Fatal(err)
			}
			if _, err := Parse(data); err == nil {
				t.Fatal("accepted invalid contract")
			}
		})
	}
}
