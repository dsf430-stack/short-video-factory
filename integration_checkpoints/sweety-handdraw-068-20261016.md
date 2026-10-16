# Official Sweety handdraw + 068 — verified checkpoint (2026-10-16)

Status: SUCCESS. No Gemini/model API key is required by the production runner or workflow.

## Deliverable

Topic: 一滴水如何變成雨. Actual film: 29.966667 seconds, 1080×1920, 30fps, H.264/AAC, Traditional Chinese script/subtitles. Voice: unchanged existing 068 zh-TW-HsiaoChenNeural / +20% / +5Hz. Narration master: 28.473469s; full master preserved without stretching/truncation, plus official 1s cover and 0.526531s hold.

Final verified source commit: 0a2df7cd40f7daf03f083830527b8eaa85af81f3.
Final successful Actions: https://github.com/dsf430-stack/short-video-factory/actions/runs/38916904890
Final artifact: https://github.com/dsf430-stack/short-video-factory/actions/runs/38916904890/artifacts/12053040942
Artifact name: sweety-068-rain-1080x1920-38916904890. Includes film.mp4, cover, real SRT, script, acceptance and official verification records.
Final film SHA256: 19a78ebac5cb6cabd5b637f9c379b9da63b957d885389421f8a7c5baf970648a.

## Implementation and use

Workflow: .github/workflows/sweety-handdraw-068.yml (manual topic input). Runner: handdraw/produce.py. Catalog: handdraw/prepared/catalog.json. Instructions/sources: handdraw/README.md.

The assistant prepares scripts, original illustrations, drawing plans, actual source-image reviews and semantic polygons using existing ChatGPT capabilities. Actions consumes these prepared jobs, reuses smart_voice/generate_voice.py, and calls the unchanged complete official engine pinned at 5206ec0d17f9b353e400b64b9c51ad69e721e02a (including its five bundled dependencies). Unknown topics fail explicitly until a new bundle is prepared; they do not silently reuse a film. Existing voice code and existing workflows are unchanged. No social publication.

## Actual validation

- Existing 068: 7 tests; official upstream: 59 tests; offline official smoke passed earlier. Do not repeat solved checks without a relevant change.
- Four actual final illustrations pass official semantic ownership, lifted-stroke, nib/paint coverage and outline-before-fill checks.
- Actual production doctor/build/render/verify and SHA-bound finalize pass. Finalization replay reused the same verified film bytes.
- Downloaded the actual artifact and verified its SHA. Inspected final decoded frames at 6s,26s,28.5s,28.8s and the original cover/illustrations. Official pen scale reduced to 0.25 after the original larger pen intersected captions; actual corrected frames show clearance.
- Full decode, H264/AAC, complete voice timeline, real SRT boundaries, single burned subtitle layer, bounds/glyph isolation and ending guards pass.
- Audio: -17.17 LUFS, -6.77dBTP, PCM correlation 0.9999464479, last-phrase correlation 0.9999662066, tail 1.196531s. Human subjective listening/phone preference remains UNCERTAIN and is explicitly retained in review limitations. No BGM.

## Resolved causes — do not repeat

The abandoned model-dependent prototype hit Gemini 404 and repeated 503/high demand. User requested no unnecessary Gemini dependency; the entire model dependency was removed from the entry/workflow. Do not ask for a new Gemini key or restore that dependency.

Existing 068 transient 429 recovered by cooling down and resuming the same endpoint/voice. First prepared voice was 29.152653s, too long with the official cover; four script characters were removed naturally and a new 28.473469s recording was verified. Do not change speed/pitch/voice or reuse the longer voice with the shorter script. A missing re import was fixed and the real SRT parser was tested. The pen-caption intersection was fixed by the single pen-scale change; reviewed film SHA above is authoritative.

## Remaining boundary

No core blocker for this prepared example. New topics require assistant preparation/review before Actions. Rendering and narration caches are hash-bound and resumable. Main/default branch manual entry should be read back after PR merge. Do not claim an Electron app UI was added.
