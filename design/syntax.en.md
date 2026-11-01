# Language-neutral highlighting analysis specification

[한국어 (default)](syntax.md) · **English**

0.9.0 TVR-24 follow-up. [Usage/examples/editor migration](../docs/syntax.en.md) · [Shared fixtures](syntax-cases.json) · [Shared SQL vocabulary](sql-syntax-words.json). SDK language and analyzed source language are independent.

| Layer | SDK owns | Host owns |
| --- | --- | --- |
| Tokens | Original UTF-8 byte [start,end), roles, language/dialect, exact-source validation | Source and language/dialect choice |
| Optional analysis | Oracle SQL/PLSQL lexer and custom injection API | Custom analyzer, workers/scheduling |
| Rendering | Graphemes/cells/CJK, palettes, state/scroll/editing | Composition/global keys/search query |
| Business | None | Execution/dangerous SQL/transactions/DB/Oracle metadata |

Core does not require every source analyzer. Go selects analysis through root API calls and initializes vocabulary at construction. Rust syntax-sql is default-off, independent of rendering features. No new runtime/native-tool/database dependency. Preserve a value contract suitable for future Python/JS/TS/C/C++ adapters.

## Tokens and application

Source is unchanged; tokens are ordered nonoverlapping positive-length byte ranges. Whitespace may be omitted; rendering inserts no tags. Validate exact source/ranges and apply atomically. Existing SetByteSyntax retains strict grapheme boundaries. Builtin analysis assigns an entire grapheme the role of its first intersecting token; byte/grapheme/cell units remain distinct.

Initial binding failures preserve existing state. Failures after edits clear stale highlighting and expose an error. Cache successful/failed source until it changes or an explicit reset. Apply results/callbacks on the UI execution flow. Hosts choosing asynchronous analysis submit source-tagged results; reject stale results. Secret mode skips automatic analysis and hides source caches from diagnostics.

## Roles and fallback

| Semantic role | Render family | Existing palette foreground |
| --- | --- | --- |
| keyword | syntax.keyword | info |
| function, macro, attribute | syntax.function | success |
| type | syntax.type | header |
| string, character | syntax.string | warning |
| number, constant | syntax.number | edited |
| comment, directive | syntax.comment | hint |
| parameter, lifetime | syntax.parameter | error |
| identifier, operator, punctuation, unsupported | body | body |

Apply contrast rules and bind foregrounds to the actual surface. No per-language palette. Preserve existing Go SyntaxKind numbers; 0.9.2 improves dark/8 colors/attributes in Go/Rust semantic editors and the Go SyntaxStyleFunc adapter. Precedence: disabled > selection > search (edited) > syntax > body; cursor focus decoration retains the winning background. Source changes expire search matches. Apply consistent dark/light/monochrome × 8/16/256/True Color and Unicode/ASCII behavior.

## Implemented: Oracle SQL/PLSQL

Classify keywords, known builtins/types, normal/N/q/nq strings, numbers, comments, binds, identifiers/operators/punctuation. Quoted identifiers remain identifiers. Keywords inside strings/comments are not reclassified. Oracle block comments end at the first terminator rather than nesting. Unfinished strings/comments retain the remaining source under their role. The fixed minimum highlighting vocabulary does not promise complete schemas/versions or semantic analysis; unknown names are not guessed to be functions/types.

[Oracle literals](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Literals.html) · [PL/SQL lexical units](https://docs.oracle.com/en/database/oracle/oracle-database/21/lnpls/plsql-language-fundamentals.html). Own AGPL-3.0-only implementation, unrelated to execution safety validation.

## Future source-language classifications: analyzers not implemented

| Language | Minimum rules |
| --- | --- |
| Go | func/package/if keywords; contextual calls/known builtins functions and contextual int/string/declared types. Variables identifiers; true/false/nil constants. Quoted/backtick strings, rune characters, integer/float/imaginary numbers. Line/block comments, build directives. Parameter names only with context; identifier otherwise. |
| Rust | fn/let/impl/match keywords; contextual calls/types and variable/raw identifiers. Boolean constants; normal/raw/byte strings and character/byte-character literals. Line/nested block comments; println! macros, derive attributes and lifetimes distinguished from characters. |

Future fixtures cover generics, raw/multiline strings, fake keywords in comments and incomplete input. Current SQL analysis rejects Go/Rust requests; plans are not claimed implemented. Extend shared role/range/fallback, literal edit/undo/selection and performance conformance when adding languages.

## Validation and performance

Shared fixtures separate exact SQL byte/role expectations, valid UTF-8 incomplete prefixes, seventeen role fallbacks and future-language examples. Both SDKs consume the same fixtures. Validate 10,000-line analysis/application/scroll/original preservation and record actual measurements in [evidence](../docs/evidence/syntax-results.json). Analysis and Layout visit the full source; no incremental parser/rope. Distinguish Go post-Show/Rust TestBackend/real PTY checks from unrun remote CI/publication.
