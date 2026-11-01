// TUIVORY is a DB-free, interactive component and theme playground.
package main

import (
	"fmt"
	"github.com/leechis7/tuivory/go/internal/showcase"
	"os"
)

func main() {
	if err := showcase.Run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
