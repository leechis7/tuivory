// Run this example directly, or select it with tuivory --demo catalog.
package main

import (
	"github.com/leechis7/tuivory/go/internal/showcase/catalog"
	"os"
)

func main() { catalog.Run(os.Args[1:]) }
