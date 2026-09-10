# Kids English Video Factory

Goal: turn one English word into a short vertical learning video with minimal manual work.

## Pilot

The first preset is `presets/potato.json`.

Pipeline:

1. Load a word preset.
2. Generate or import one visual asset per shot while keeping the character/style consistent.
3. Generate English narration with the existing Edge TTS module.
4. Generate timed English subtitles from narration segments.
5. Render 1080x1920 (9:16) video with the existing FFmpeg/effect-engine pipeline.
6. Export MP4.

## POTATO acceptance criteria

- 10-second vertical video.
- Three shots at 0-3s, 3-6s, and 6-10s.
- Stable cute potato character in children's crayon picture-book style.
- Capital P appears first, then expands to POTATO.
- English child-friendly narration and readable subtitles.
- Final output is a standard MP4 suitable for Shorts/Reels/TikTok.

This directory is intentionally isolated from the upstream application while the pilot is validated. After validation, the preset loader and one-click Kids English mode can be wired into the existing Home/TTS/render modules.
