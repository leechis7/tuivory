// Package terminal exposes screen, key, pointer, color and style compatibility
// through Tuivory. Aliases preserve native callbacks and screen implementations.
// Variables are startup values (maps share backend entries); rebinding a facade
// variable does not rebind a backend global. Use explicit configuration functions.
package terminal
