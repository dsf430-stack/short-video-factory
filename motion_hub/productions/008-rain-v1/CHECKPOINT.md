# 008 rain v1 — FAILED; awaiting user confirmation of minimal repair
Catalog: lemo-opuscar:dark-keynote
Source: fdc46d7f0e20cc953a71d56241a92d1b4cb7298e
Branch: test/008-rain-068-v1
Target: 30s / 1080x1920 / 30fps / 068 narration / Traditional Chinese.

Completed: pinned sources fetched; official guides and engine read; original treatment and animated scene code written; original engine copied with only local import and portrait dimensions adapted; real 068 voice generated successfully (24.737959s, full decode pass, measured -13.38 LUFS, -1.24 dBTP); font coverage verified.
Actual render failure: ValueError: FAILED: nondeterministic page.
Root cause isolated by read-only runtime diagnostic: upstream lightReveal reuses reveal/reveal2 offscreen canvases without clearRect. Transparent pixels retain previous scene content. Rendering t=1 → t=0 → t=1 gives different screenshots. Clearing just reveal/reveal2 buffers before each call in an ephemeral diagnostic gives identical screenshots. No source fix applied.
Proposed repair: two clearRect calls in the production-local engine.js only. Exact patch: proposed-buffer-fix.patch. User project requires confirmation before bug fixes; pause before applying.
Diagnostic frame at 16s inspected: Chinese fonts readable, particle coalescence and accent drop present. Not a successful film; output MP4 not yet rendered. Voice listening, film_gate, full film review and user viewing all unconfirmed.
Remaining: apply confirmed patch; repeat 3 style frames; shift narration by 1s; generate quiet score and sound effects, mix/pad to30s; render; film_gate; decode and sample frames; persist MP4+assets; update ledger.
Actions: no 008 run started; existing integration SUCCESS is not this film.
Next number after 008 completion:009. Never mark 008 passed without full verification.
