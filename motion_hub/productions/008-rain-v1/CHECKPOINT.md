# 008 rain v1 — FAILED (quality gate), technical PASS
Date:2026-10-15. Branch:test/008-rain-068-v1. Catalog:lemo-opuscar:dark-keynote.
Source:fdc46d7f0e20cc953a71d56241a92d1b4cb7298e.
User approved the diagnosed two-line local buffer fix; applied and deterministic render PASS.
MP4 actually rendered locally using existing motion_hub/render.py, not GitHub Actions. Main/068 source unchanged. No merge, publication or paid API.
MP4:008-rain-v1.mp4. 30.000s,1080x1920,30fps,H264/AAC. Audio30s, full decode PASS, no black segments. Voice real068,24.737959s,+20%,+5Hz,offset1s; no truncation. Narration saved in Library libfile_64fe425a5fe081919b30831ddea94859 and reused.
Final audio measured -13.91LUFS,-0.88dBTP; peak misses source <=-1 target by0.12dB. Not clipping.
Final encoded frames at1.5,6,11,16,19.5,23,28s inspected; CJK readable. Style: nearblack grid, original UI panels, one mint accent, light sweep, toast captions.
film_gate actually executed:RED,fast_ratio0.0,page_frame_share0.933; blank_run_s0,blue_purple_share0.017. Animated objects exist, but motion amplitude insufficient for this metric. Do not claim film_gate PASS.
Full-speed sound viewing, subjective listening, independent MG scoring and user acceptance:UNCERTAIN/PENDING.
User-facing verdict:008 FAILED quality gate, technical PASS.009 UNTESTED. Wait for review; don't automatically run009.
Proposed v2 (await confirmation per user bug/failed-QA rule): amplify meaningful coalescence/falling-water movement; remove excessive persistent frame; preserve engine/audio/topic; lower mix true-peak target by0.3dB and check encoded AAC. Do not lower quality thresholds. Preservev1.
See final-qa.json,film-gate.json,驗證結果.md and encoded-contact-sheet.png. Build recipe and local font subsets committed with source. Technical proof is not artistic/user approval.

Saved film Library ID:libfile_c3420a9c9be88191921c271ad33358c0. Media+QA archive:libfile_1009c668acac81919f3da9ef09e07df3. Both saved successfully; source remains in GitHub branch.
