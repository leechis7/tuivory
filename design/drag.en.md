# Movement requests and drag rules

[한국어 (default)](drag.md) · **English**

0.10.0 TVR-18 specification. [Usage/API integration/examples/screens](../docs/drag-drop.en.md), [shared acceptance cases](drag-cases.json).

| Stage | Data/selection/focus | Capture/feedback |
| --- | --- | --- |
| down/armed | Unchanged | Capture movable source ID and model/state/viewport versions |
| move/dragging | Unchanged | Default maximum-axis distance of two cells; resolve target, position and eligibility |
| up/drop | Unchanged | Revalidate current data/policy, emit one request and release capture |
| reject/cancel/stale | Unchanged | Clear preview/capture; no request |
| Host approval/application | Host replaces immutable model | Retain stable active/focus IDs, metadata and subtrees |

Raw IDs/coordinates are not persistence commands. Requests describe the current in-process model; no OS/external-app/file/DB movement is executed. Model revisions use UTF-8 byte-length prefixes with 64-bit FNV-1a; equivalent Go/Rust data uses the same value. Check application policy at request time and final approval.

Pointer coordinates are inner-viewport cells; continue outside move/up while captured. Cancel for changed model/original state/viewport/theme. Hosts cancel hidden non-rendering components and capture loss. Preview scroll/expansion is independent from real state and defaults off; configure one-item-per-edge-move scroll and immediate allowed-branch hover expansion. Own no timer or global keys.

Insertion markers plus bold/underline distinguish eligibility in monochrome and eight colors. Info/error foregrounds follow ordinary text contrast on the actual surface. Provide Unicode `│ ↑ ↓ ↳`, ASCII `| ^ v +`, and rejection `!`, without ordinary disabled prefixes. Existing cell-width/truncation rules apply; draw feedback in reserved marker cells or tab edges.

Persistence/business permission/transaction/global focus and shortcuts remain application responsibilities.
