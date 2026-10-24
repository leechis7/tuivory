// Output the same language-neutral palette as the Python and Node.js consumers.
package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/leechis7/tuivory/go"
)

func main() {
	theme, profile := "dark", "256"
	if len(os.Args) == 3 {
		theme, profile = os.Args[1], os.Args[2]
	}
	d, err := tuivory.CandidateTokens()
	if err != nil {
		fail(err)
	}
	p, err := d.Palette(theme, profile)
	if err != nil {
		fail(err)
	}
	if err := json.NewEncoder(os.Stdout).Encode(p); err != nil {
		fail(err)
	}
}

func fail(err error) { fmt.Fprintln(os.Stderr, err); os.Exit(1) }
