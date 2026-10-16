# Sweety handdraw integration checkpoint — 2026-10-16

Status: IN_PROGRESS, NOT COMPLETE. Draft PR #4. Latest state is in the continuation below.

Read latest main 8def626c8a2c04b53311b600c6e4debca84754c6, README, existing Actions, actions-request bridge, smart_voice generator and voices.json. AGENTS.md and PROJECT_STATUS.md are absent at main root. Existing motion-hub remains on its separate branch; it was not replaced or merged.

Official source read: README.md, skills/sweety-handdraw-video/SKILL.md, runtime-contract, drawing/style, continuous narration, story design, dependency routing and production validators. Pin: 5206ec0d17f9b353e400b64b9c51ad69e721e02a. Full repository is fetched by the isolated workflow, including its bundled dependencies; no official validators are bypassed.

Existing 068 is zh-TW-HsiaoChenNeural / +20% / +5Hz. Existing voice implementation and workflows unchanged.

Actual run 38905654953, job 116988438504 failed at Check configured model connection: GEMINI_API_KEY and GOOGLE_API_KEY both resolve to empty in this job. This only establishes these two names are unavailable to this workflow, not that the account has no key elsewhere. Connector cannot read secret values. Do not ask user to paste keys into chat or commit credentials.

New workflow: .github/workflows/sweety-handdraw-068.yml, branch integration/sweety-handdraw-068. Supports manual topic input and branch push preflight. Separate official-runtime job verifies official regressions/smoke and existing 068 tests independently of the credential check. Smoke video is a fixture and must never be delivered as the requested story. This workflow is a preflight only; it does NOT yet implement topic-to-production-video automation.

Remaining: connect an authorized model credential; implement model-authored script, style/drawing plan, guided images and real visual reviews, measured narration alignment via existing 068 SRT, production job build, official render/verify, 1080x1920/30s MP4 checks and final artifact upload. Preserve all official production gates. Test case: 一滴水如何變成雨. No final MP4/artifact exists. Keep PR draft, do not merge or report complete.

## Verified independent results

Run 38905748444: official-runtime SUCCESS. Existing 068: 7 tests passed; official upstream: 59 tests passed; official offline animation smoke passed, including H.264/AAC full decode and fixture delivery rejection. Evidence artifact 12048331571 contains reports only, NOT the requested MP4. model-connection failed due to the two unavailable secret names. No retry without a relevant configuration change.

## Continuation after repository key configuration (21:32–21:56 Taipei)

User configured the repository secret. Rerun 38905748444 verified real Gemini authentication; missing-key blocker is resolved.

Production adapter handdraw/produce.py now connects real model-authored storyboard/drawing plan, guided image generation and image reviews, unchanged smart_voice/generate_voice.py 068, actual SRT-boundary alignment, unchanged official production doctor/build/render/verify/finalize, exact 30s 1080x1920/30fps acceptance, and final Actions artifact upload. It is IMPLEMENTED BUT NOT END-TO-END VERIFIED. Do not claim completion or merge yet.

Actual failures and minimal changes:
- gemini-2.5-flash returned 404 despite the API still advertising it. Model selection now requires an actual structured generation probe, not merely models.list.
- 3.8/3.5/flash-latest returned 503 UNAVAILABLE high demand. gemini-3-flash-preview passed real probes and generated a full storyboard. Repeated full-call 503 remains transient; provider cooldown now respects Retry-After, otherwise 30/60 seconds, up to three attempts.
- Reduced duplicate CLI/runtime documentation in creative prompts while retaining full art guide + story/drawing guidance and all unchanged official validators.
- Generated outline/fill ID arrays disagreed with the actual model-authored parts. Adapter now derives both execution orders from that existing semantic parts list, without bypassing verification.
- Initial 068 request returned websocket 429. Cooldown/resume with same endpoint and voice succeeded in run 38911055209 attempt 2: new narration 30.458776 seconds, CHUNK 1/1 SUCCESS. This is genuine new speech, not the old sample.
- Need narration about 28.5 seconds so the fixed 1-second cover and 0.2–0.8-second ending fit the 30-second film. Script revision request hit provider 503 after first narration; completed voice/model work is cached for resume.

Latest production code commit at this point: b1989aeb90d8be772e3749234405755d09887c7e. Latest run: 38911527834 (in progress at checkpoint). Image generation/render/final MP4 remain unverified. Existing 66 regressions and official smoke already passed earlier; do not repeat them without cause. No final video download exists yet. Continue the current run, inspect actual failed step/log, and make only the evidenced minimal correction. Never deliver smoke fixtures or fabricate visual review pass records.
