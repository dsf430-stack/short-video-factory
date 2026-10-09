# Smart Voice Library / 智慧配音庫

This is an additive component for the existing short-video-factory. It does not publish videos or change the existing video pipeline.

Voice IDs: M01–M05 (male), F01–F05 (female), 068 (existing HsiaoChen preset). IDs are **provisional until auditioned**. M02 here is a newly assigned English preset, **not a verified reproduction of any historical M02 audio**.

Install missing dependency only: `python -m pip install edge-tts`.

Generate narration:

```bash
python smart_voice/generate_voice.py --voice-id F01 --text "Did you know octopuses have three hearts?" --output narration.mp3
```

Automatically choose a voice from topic/language:

```bash
python smart_voice/generate_voice.py --voice-id auto --topic "science facts" --language en --text "Sound travels faster in water." --output narration.mp3
```

The caller can pass scene-by-scene text and combine generated MP3s with existing subtitle, BGM and FFmpeg steps. Topic selection is deterministic keyword matching, not emotional AI voice acting. The 068 preset uses +20% rate and +5Hz pitch for Chinese; English presets use +0% rate. Actual voice availability and audio QA require runtime Edge TTS connectivity.
