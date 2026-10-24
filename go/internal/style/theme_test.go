package style

import (
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"

	"github.com/gdamore/tcell/v2"
)

// Fixture captured by executing the original LazyOra palette/token functions,
// without database or screen dependencies. See docs/lazyora-extraction.md.
func TestStylesMatchLazyOraSource(t *testing.T) {
	data, err := os.ReadFile("testdata/lazyora-styles.json")
	if err != nil {
		t.Fatal(err)
	}
	var expected map[string]map[string]tcell.Color
	if err := json.Unmarshal(data, &expected); err != nil {
		t.Fatal(err)
	}
	for key, fields := range expected {
		t.Run(key, func(t *testing.T) {
			parts := strings.Split(key, "-")
			s, err := NewStyles(parts[0], parts[1])
			if err != nil {
				t.Fatal(err)
			}
			actual := map[string]tcell.Color{}
			values := []reflect.Value{reflect.ValueOf(s.Colors), reflect.ValueOf(s)}
			for _, value := range values {
				for i := 0; i < value.NumField(); i++ {
					if value.Field(i).Kind() != reflect.Uint64 {
						continue
					}
					name := value.Type().Field(i).Name
					actual[strings.ToLower(name[:1])+name[1:]] = tcell.Color(value.Field(i).Uint())
				}
			}
			if !reflect.DeepEqual(fields, actual) {
				t.Fatalf("source style mismatch\nexpected %v\nactual %v", fields, actual)
			}
		})
	}
}

func TestProfileDetectionAndInvalidOptions(t *testing.T) {
	for _, c := range []struct {
		count   int
		limited bool
		want    string
	}{
		{0, false, "truecolor"}, {8, false, "8"}, {16, false, "16"}, {256, false, "256"}, {1 << 24, false, "truecolor"}, {8, true, "8"}, {256, true, "16"},
	} {
		if got := ProfileForColors(c.count, c.limited); got != c.want {
			t.Fatalf("profile %d/%t: %s", c.count, c.limited, got)
		}
	}
	if _, err := NewStyles("unknown", "8"); err == nil {
		t.Fatal("invalid theme accepted")
	}
	if _, err := NewStyles("dark", "auto"); err == nil {
		t.Fatal("unresolved profile accepted")
	}
}
