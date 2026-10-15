# 038 active render

- Run: https://github.com/dsf430-stack/short-video-factory/actions/runs/38773124258
- Job: 116553805918
- Render commit: 0b6b46d4f70071408548562684fc02686ee88611
- State at this checkpoint: IN_PROGRESS, render step active. No MP4 delivered yet.
- Fixed workflow literal newline escapes (previously invalid YAML).
- Edge TTS 7.2.8 returned HTTP 429; isolated workflow dependency updated to official 7.3.1. Same 068 voice generation then succeeded.
- Original pinned Lemo Three.js and tilt-shift post.js loaded successfully.
- Existing renderer is producing 1200 frames, 1080x1920, 30fps, 40 seconds, with generated 068 narration.
- Do not restart this job merely because connector dispatch is unavailable. Poll existing run, obtain artifact, decode/probe, inspect frames/audio, save final MP4, then deliver.
- This active run uses motion_hub/render.py with native Three.js scene and official post.js; it does not use upstream core/render/video.mjs worker scheduler. Do not claim otherwise.
- Earlier Canvas substitute is rejected per prior checkpoint; never deliver it as official 038.
