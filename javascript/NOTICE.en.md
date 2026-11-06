# Tuivory TypeScript / JavaScript — notices

[한국어 (기본)](NOTICE.md) · **English**

This language implementation is independently written for Tuivory under AGPL-3.0-only. It does not link/call another Tuivory language implementation.

Unicode width/grapheme data and adapted width algorithms derive from wcwidth 0.9.4 (Unicode 18.0.0), MIT and Markus Kuhn notices. See [UNICODE-LICENSE](UNICODE-LICENSE); shared source in design/. Python uses ordinary regex/wcwidth dependencies; other languages use their own width/segmentation implementations and embedded data.

Search case folding embeds the Unicode17 default full C+F mapping under [Unicode License V3](CASEFOLD-LICENSE). It excludes the Turkic override and performs no normalization. The original source URL/hash are recorded in design/casefold.json.
