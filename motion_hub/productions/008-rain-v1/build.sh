#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
production=motion_hub/productions/008-rain-v1
if [ ! -f "$production/narration.mp3" ]; then
  python smart_voice/generate_voice.py --voice-id 068 --text-file "$production/narration.txt" --output "$production/narration.mp3"
fi
python "$production/mix_audio.py"
if [ ! -f "$production/008-rain-v1.mp4" ]; then
  python motion_hub/render.py "$production/index.html" "$production/008-rain-v1.mp4" --duration 30 --fps 30 --size 1080x1920 --audio "$production/mix.wav"
fi
python motion_hub/.sources/huashu-art-motion/scripts/film_gate.py "$production/008-rain-v1.mp4" --no-template --json > "$production/film-gate.json"
