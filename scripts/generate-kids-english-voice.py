#!/usr/bin/env python3
"""Generate a natural, timed Kids English narration with Edge Neural TTS."""

import argparse
import asyncio
import subprocess
import tempfile
from pathlib import Path

import edge_tts


SEGMENTS = (
    ("P is for potato!", 250),
    ("P. O. T. A. T. O!", 3200),
    ("Potato! Great job!", 6500),
)
PREFERRED_VOICES = ("en-US-AnaNeural", "en-US-JennyNeural", "en-US-AriaNeural")


async def select_voice(requested: str | None) -> str:
    available = {voice["ShortName"] for voice in await edge_tts.list_voices()}
    if requested:
        if requested not in available:
            raise RuntimeError(f"Edge voice is unavailable: {requested}")
        return requested
    for voice in PREFERRED_VOICES:
        if voice in available:
            return voice
    fallback = next((voice for voice in available if voice.startswith("en-US-")), None)
    if not fallback:
        raise RuntimeError("No en-US Edge Neural voice is available")
    return fallback


async def render(output: Path, requested_voice: str | None) -> None:
    voice = await select_voice(requested_voice)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kids-english-voice-") as temp:
        temp_dir = Path(temp)
        clips = []
        for index, (text, _) in enumerate(SEGMENTS):
            clip = temp_dir / f"segment-{index}.mp3"
            communicate = edge_tts.Communicate(text, voice, rate="-8%", pitch="+2Hz", volume="+0%")
            await communicate.save(str(clip))
            clips.append(clip)

        filters = []
        labels = []
        for index, (_, delay_ms) in enumerate(SEGMENTS):
            label = f"a{index}"
            filters.append(
                f"[{index}:a]adelay={delay_ms}|{delay_ms},"
                "highpass=f=90,lowpass=f=10000,acompressor=threshold=-18dB:ratio=2:attack=20:release=180"
                f"[{label}]"
            )
            labels.append(f"[{label}]")
        filters.append(
            f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,"
            "apad=pad_dur=10,atrim=duration=10,loudnorm=I=-16:TP=-1.5:LRA=9[a]"
        )

        command = ["ffmpeg", "-y"]
        for clip in clips:
            command.extend(["-i", str(clip)])
        command.extend(
            [
                "-filter_complex", ";".join(filters),
                "-map", "[a]", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", str(output),
            ]
        )
        subprocess.run(command, check=True)
    print(f"Created natural narration with {voice}: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="assets/kids-english/potato-narration.m4a")
    parser.add_argument("--voice", default=None)
    args = parser.parse_args()
    asyncio.run(render(Path(args.output), args.voice))


if __name__ == "__main__":
    main()
