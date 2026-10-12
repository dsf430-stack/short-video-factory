# HyperFrames 068 integration test — 2026-10-12
Status: SUCCESS (technical render/audio/motion); UNCERTAIN (subjective listening/mobile playback).
Branch: test/hyperframes-068. Main untouched; inherited base d67fc84c1969395ba1506f64bbbd3536a8b7e4b7.
Verified execution commit: 257aa5759d1c2f490ed819e6a6a04d224e500206.
Run: https://github.com/dsf430-stack/short-video-factory/actions/runs/38241771943
Artifact: https://github.com/dsf430-stack/short-video-factory/actions/runs/38241771943/artifacts/11742069927
Artifact retention: 14 days; archive contains MP4, original picture MP4, narration MP3/SRT/JSON, logs, FFprobe JSON, QA JSON, snapshots, lockfile, official README and checkpoint.
HyperFrames source: 86521b94f592bcf0ca86aba63068893cf658af16; npm installed hyperframes 0.8.149.
Official commands: npx hyperframes init whiteboard; npx hyperframes check; npx hyperframes render --fps 30 --quality delivery --output ../../hf-results/picture.mp4.
Rendering: beginframe capture, software GPU; 600 frames, 1080x1920, 20.000000 seconds, H264 yuv420p and AAC. Full decode passed. 36 unique sampled frames, no static-image substitution.
Final measured audio: -13.45 LUFS, -1.23 dBTP. Narration 15.124898 seconds, 1 chunk (<=300 chars), true sentence event SRT ending 15.031 seconds.
Voice: 068 / zh-TW-HsiaoChenNeural / +20% / +5Hz.
Voice source: existing smart_voice/generate_voice.py with today's verified service endpoint fix. Requested legacy generate_voices_by_chars.py is absent from current main; this test did not claim to execute that filename.
Final MP4 SHA256: 82f999db8828296bfb139ee2e2a587ed1acc6ada8f70ab38fa1296375e2a4cea.
Visual inspection: frames 11 and 16 inspected; visible drawing/checkmark/pen animation and readable Traditional Chinese text/subtitles. Subjective audio audition unavailable.

## Failures and lessons
Previous container checkpoint: GitHub/npm DNS and direct IP connectivity failed. Resolved execution placement: GitHub-hosted Actions successfully downloaded source, npm/Python packages and Chrome; do not retry prior failed container network routes.
Run 38241676709: cp: cannot stat '../hyperframes_test/index.html': No such file or directory. Root cause: workflow committed before input files; fixed by completing input commits. Run 38241769685 rendered successfully but verify.py was absent in its earlier commit (exit 2). Run 38241771943 includes all files and succeeds.
First-run failure trap used a relative hf-results path while cwd was hf-run; trap itself could not write checkpoint. Execution log and always-run final checkpoint/upload preserved failure. Future maintenance should make trap output path absolute before cwd changes.
Do not commit runnable workflow before its required files. Future multi-file changes should use one atomic tree/commit/ref update.

## Next action
Reuse successful run/artifact. No need to reinstall or rerender this test. For a new requested subject, author new isolated composition/script and reuse verified pipeline. Do not merge into main or publish social content automatically.
