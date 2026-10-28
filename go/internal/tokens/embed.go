// Package tokens contains the language-neutral reference token assets.
package tokens

import _ "embed"

// Generated asset from design/tokens/candidate.json; run tools/export_tokens.py
// from the repository root to refresh it.
//
//go:embed candidate.json
var candidateJSON string

// CandidateJSON returns the shared draft data, also read by Python and Node.js.
func CandidateJSON() string { return candidateJSON }
