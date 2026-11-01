package tuivory

import "github.com/leechis7/tuivory/go/internal/sqlsyntax"

// NewSQLAnalyzer opts into the built-in Oracle SQL/PLSQL highlighting lexer.
// It has no runtime, database, native or execution-safety dependency.
func NewSQLAnalyzer() SyntaxAnalyzer { return sqlsyntax.New() }
