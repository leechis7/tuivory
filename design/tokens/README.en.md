# Language-independent token data

[한국어 (default)](README.md) · **English**

[candidate.json](candidate.json) is reference data read by Go/Python/Node.js/Rust; [schema.json](schema.json) describes its JSON structure. The format identifier `tuivory.tokens.draft` marks a draft, not a product version. It guarantees neither DTCG compatibility nor public API stability.

```json
{
  "foreground": "7",
  "background": "0",
  "referenceForeground": "#c0c0c0",
  "referenceBackground": "#000000",
  "fontWeight": "none"
}
```

Top-level `roles` defines display order; `palettes` keys combine theme and capability, such as `dark-8`. Each palette contains every listed role exactly once. The bundled data has 3 themes × 4 profiles × 16 roles.

- `foreground`/`background`: normalized decimal index strings or `#RRGGBB`. Profiles 8/16/256 allow indices 0–7/15/255 respectively. Truecolor accepts RGB and indices 0–255.
- `referenceForeground`/`referenceBackground`: reference RGB for validation; these do not replace the user's ANSI palette.
- `fontWeight`: `none` or `bold`. Validate terminals where bold selects brighter colors separately.

The schema checks structure. Matching role sets and profile-specific color ranges require semantic checks, performed by Go's `tuivory.ParseTokens` and Rust's `TokenDocument::from_json`. JSON object property names must not repeat.

## Candidate sources and generation

The candidate is generated from the [source CSV](../themes/lazyora-candidate.csv), design review material derived from LazyOra rather than a mandatory default for all applications. Edit the CSV and regenerate JSON when changing this candidate. Additional themes can use independent documents with the same format.

```sh
python3 tools/export_tokens.py
python3 tools/export_tokens.py --check
```

Shared JSON stays here; Go source does not. The exporter writes identical content to `go/internal/tokens/candidate.json` and `rust/src/data/candidate.json` for independent distribution and embedding. Do not edit that generated copy manually. `--check` compares CSV, shared JSON, and the Go/Rust copies. Go/Rust projects need no other repository directories; Python and JavaScript read the shared source directly.

Distinguish raw role backgrounds from actual component surfaces. Bind plain text to its real surface and check foreground contrast there; preserve explicit field/selection/edit/custom backgrounds. [Surface rules](../surfaces.en.md).
