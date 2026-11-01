// Package sqlsyntax is an optional, dependency-free highlighting tokenizer.
// It is not an execution parser, permission check or SQL safety classifier.
package sqlsyntax

import (
	"encoding/json"
	"fmt"
	"github.com/leechis7/tuivory/go/internal/highlight"
	"github.com/rivo/uniseg"
	"strings"
	"unicode"
	"unicode/utf8"
)

// Analyzer classifies Oracle SQL and PL/SQL without modifying source.
type Analyzer struct{ keywords, functions, types map[string]bool }

func New() *Analyzer {
	var data map[string][]string
	if err := json.Unmarshal([]byte(wordJSON), &data); err != nil {
		panic(err)
	}
	makeSet := func(names []string) map[string]bool {
		m := map[string]bool{}
		for _, name := range names {
			m[name] = true
		}
		return m
	}
	return &Analyzer{keywords: makeSet(data["keywords"]), functions: makeSet(data["functions"]), types: makeSet(data["types"])}
}
func (a *Analyzer) AnalyzeSyntax(text string, request highlight.Request) (highlight.Analysis, error) {
	language, dialect := strings.ToLower(request.Language), strings.ToLower(request.Dialect)
	if language == "" {
		language = "sql"
	}
	if dialect == "" {
		dialect = "oracle"
	}
	if (language != "sql" && language != "plsql") || dialect != "oracle" {
		return highlight.Analysis{}, fmt.Errorf("unsupported syntax language/dialect: %s/%s", language, dialect)
	}
	if !utf8.ValidString(text) {
		return highlight.Analysis{}, fmt.Errorf("syntax source must be UTF-8")
	}
	result := highlight.Analysis{Source: text, Language: language, Dialect: dialect, Tokens: []highlight.Token{}}
	for i := 0; i < len(text); {
		start := i
		r, n := utf8.DecodeRuneInString(text[i:])
		if unicode.IsSpace(r) {
			i += n
			continue
		}
		role := "punctuation"
		switch {
		case strings.HasPrefix(text[i:], "--"):
			role = "comment"
			i += 2
			for i < len(text) && text[i] != '\n' && text[i] != '\r' {
				i++
			}
		case strings.HasPrefix(text[i:], "/*"):
			role = "comment"
			if end := strings.Index(text[i+2:], "*/"); end >= 0 {
				i += end + 4
			} else {
				i = len(text)
			}
		case qPrefix(text[i:]) > 0:
			role = "string"
			prefix := qPrefix(text[i:])
			i += prefix
			if i < len(text) {
				open, size := utf8.DecodeRuneInString(text[i:])
				if !unicode.IsSpace(open) {
					close := open
					switch open {
					case '[':
						close = ']'
					case '{':
						close = '}'
					case '(':
						close = ')'
					case '<':
						close = '>'
					}
					i += size
					ending := string(close) + "'"
					if end := strings.Index(text[i:], ending); end >= 0 {
						i += end + len(ending)
					} else {
						i = len(text)
					}
				} else {
					i = start + n
					role = "identifier"
				}
			}
		case r == '\'' || (r == 'n' || r == 'N') && i+1 < len(text) && text[i+1] == '\'':
			role = "string"
			if r != '\'' {
				i++
			}
			i = quoted(text, i, '\'')
		case r == '"':
			role = "identifier"
			i = quoted(text, i, '"')
		case r == ':' && i+1 < len(text) && (identifierStartAt(text, i+1) || digit(text[i+1]) || text[i+1] == '"'):
			role = "parameter"
			i++
			if text[i] == '"' {
				i = quoted(text, i, '"')
			} else {
				for i < len(text) {
					c, size := utf8.DecodeRuneInString(text[i:])
					if !identifierPart(c) {
						break
					}
					i += size
				}
			}
		case strings.HasPrefix(text[i:], ".."):
			role = "operator"
			i += 2
		case digit(text[i]) || r == '.' && i+1 < len(text) && digit(text[i+1]):
			role = "number"
			for i < len(text) && digit(text[i]) {
				i++
			}
			if i < len(text) && text[i] == '.' && !(i+1 < len(text) && text[i+1] == '.') {
				i++
				for i < len(text) && digit(text[i]) {
					i++
				}
			}
			if i < len(text) && (text[i] == 'e' || text[i] == 'E') {
				end := i + 1
				if end < len(text) && (text[end] == '+' || text[end] == '-') {
					end++
				}
				digits := end
				for end < len(text) && digit(text[end]) {
					end++
				}
				if end > digits {
					i = end
				}
			}
			if i < len(text) && strings.ContainsRune("fFdD", rune(text[i])) {
				i++
			}
		case identifierStart(r):
			i += n
			for i < len(text) {
				c, size := utf8.DecodeRuneInString(text[i:])
				if !identifierPart(c) {
					break
				}
				i += size
			}
			word := asciiUpper(text[start:i])
			role = "identifier"
			if a.types[word] {
				role = "type"
			} else if a.functions[word] {
				role = "function"
			} else if a.keywords[word] {
				role = "keyword"
			}
		default:
			i += n
			if strings.ContainsRune("+-*/%=<>!|:^~", r) {
				role = "operator"
				if i < len(text) && containsPair(text[start:i+1]) {
					i++
				}
			}
		}
		result.Tokens = append(result.Tokens, highlight.Token{Start: start, End: i, Role: role})
	}
	// A display grapheme receives the role of its first intersecting token.
	// This keeps punctuation/emoji/combining sequences on exact adapter boundaries.
	aligned := []highlight.Token{}
	g := uniseg.NewGraphemes(text)
	at := 0
	lastToken := -1
	for g.Next() {
		start, end := g.Positions()
		for at < len(result.Tokens) && result.Tokens[at].End <= start {
			at++
		}
		if at < len(result.Tokens) && result.Tokens[at].Start < end {
			if lastToken == at && len(aligned) > 0 && aligned[len(aligned)-1].End == start {
				aligned[len(aligned)-1].End = end
			} else {
				aligned = append(aligned, highlight.Token{Start: start, End: end, Role: result.Tokens[at].Role})
			}
			lastToken = at
		} else {
			lastToken = -1
		}
	}
	result.Tokens = aligned
	return result, nil
}
func digit(b byte) bool { return b >= '0' && b <= '9' }
func asciiUpper(text string) string {
	b := []byte(text)
	for i, c := range b {
		if c >= 'a' && c <= 'z' {
			b[i] = c - 'a' + 'A'
		}
	}
	return string(b)
}
func identifierStart(r rune) bool { return unicode.IsLetter(r) || r == '_' }
func identifierPart(r rune) bool {
	return identifierStart(r) || unicode.IsDigit(r) || unicode.IsMark(r) || r == '$' || r == '#'
}
func identifierStartAt(s string, i int) bool {
	r, _ := utf8.DecodeRuneInString(s[i:])
	return identifierStart(r)
}
func quoted(s string, i int, quote byte) int {
	i++
	for i < len(s) {
		if s[i] == quote {
			i++
			if i < len(s) && s[i] == quote {
				i++
				continue
			}
			return i
		}
		i++
	}
	return i
}

// Prefix length includes the opening apostrophe, but not the delimiter.
func qPrefix(s string) int {
	if len(s) >= 3 && (s[0] == 'q' || s[0] == 'Q') && s[1] == '\'' {
		return 2
	}
	if len(s) >= 4 && (s[0] == 'n' || s[0] == 'N') && (s[1] == 'q' || s[1] == 'Q') && s[2] == '\'' {
		return 3
	}
	return 0
}
func containsPair(s string) bool {
	switch s {
	case ":=", "=>", "<=", ">=", "!=", "<>", "||", "**":
		return true
	}
	return false
}
