# yovoice 繁體中文 CPU 配音測試

- Branch: feature/yovoice-tts-test; main and all existing production files unchanged.
- Official CLI v0.2.1 Linux x64; archive SHA256 checked against official Release digest.
- Ubuntu 24.04; official setup downloaded audio.cpp v0.9.1 CPU engine.
- Model: kokoro-1.1-zh-q8; speaker: zf_001; model downloaded from Hugging Face and verified by CLI.
- Input: 你知道嗎？颱風的英文叫做 Typhoon。今天我們用三十秒，了解颱風是怎麼形成的。
- Run SUCCESS: https://github.com/dsf430-stack/short-video-factory/actions/runs/39106843053
- Audio: test-tw.wav, 7.45 seconds, pcm_s16le, 24000 Hz, mono, 357644 bytes.
- SHA256: 15a570548298b30d85ff18379c5925b244ac330ea4f35396ef4b28c658b8a745
- ffprobe and full ffmpeg -xerror decode passed in Actions and after download.
- Artifacts: https://github.com/dsf430-stack/short-video-factory/actions/runs/39106843053/artifacts/12128513970 ; WAV, narration, model inventory, generation JSON, ffprobe JSON, verification JSON, CLI/engine logs. Retention 30 days.
- No paid speech API used; no production integration or changes to 068, subtitles, styles, camera movement, MP4 pipelines.
- Subjective listening, Traditional Chinese pronunciation correctness, and English Typhoon pronunciation remain NOT_VERIFIED. Audio generation/decode success is not a claim of Taiwanese accent quality.

## Integration assessment (not implemented)

CLI generates WAV and total duration, not verified word/sentence timestamps. Keep 068 as default. Before adopting yovoice, listen to this sample and validate mixed-language pronunciation. A separate adapter may return the WAV and measured duration; subtitle alignment needs a separately tested forced-alignment stage against the original Traditional Chinese transcript, with complete text coverage and timing checks. Do not infer timings from character count or replace the existing 068 boundary workflow.
