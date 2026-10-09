"""Generate voice audio using numbered presets. Requires: pip install edge-tts."""
import argparse
import asyncio
import json
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parent
VOICES = json.loads((ROOT / "voices.json").read_text(encoding="utf-8"))["voices"]

def select_voice(topic: str, language: str = "en") -> str:
    if language.lower().startswith("zh"):
        return "068"
    t = topic.lower()
    if any(x in t for x in ("history", "ancient", "historical")):
        return "M02"
    if any(x in t for x in ("science", "space", "physics", "biology")):
        return "M03"
    if any(x in t for x in ("emotional", "heartwarming", "sad")):
        return "F03"
    if any(x in t for x in ("vocabulary", "pronunciation", "english lesson")):
        return "F05"
    return "F01"

async def synthesize(text: str, output: str, voice_id: str) -> None:
    if voice_id not in VOICES:
        raise ValueError(f"Unknown voice id: {voice_id}")
    p = VOICES[voice_id]
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    await edge_tts.Communicate(text, p["voice"], rate=p["rate"], pitch=p["pitch"], volume=p["volume"]).save(str(out))
    if not out.is_file() or out.stat().st_size == 0:
        raise RuntimeError("TTS did not produce audio")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--voice-id", default="auto")
    parser.add_argument("--topic", default="")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()
    voice_id = select_voice(args.topic, args.language) if args.voice_id == "auto" else args.voice_id
    asyncio.run(synthesize(args.text, args.output, voice_id))
    print(f"voice_id={voice_id} output={args.output}")
