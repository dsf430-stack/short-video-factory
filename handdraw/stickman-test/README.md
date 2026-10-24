# Silent stickman drawing test

New code-authored stick figure, no private reference imagery. Uses unchanged official build_illustration and illustration_layers.compose at commit 3ae9b78d22af907afe70c1af4b8dc677f883bae1. Adapter omits narration, captions and soundtrack; emits 450 frames at 1080x1920, H.264. Official minimum duration and time compression are checked before encoding. This is a standalone drawing test, not the full narrated workflow's finalize certification.

Run: python handdraw/stickman-test/render.py --official /path/to/sweety --output handdraw/stickman-test/output
