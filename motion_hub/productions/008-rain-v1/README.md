# 008 rain v1
Original topic animation using pinned Lemo dark-keynote engine, portrait adaptation. Main and 068 source code unchanged.
Install `python -m pip install -r smart_voice/requirements.txt playwright==1.51.0 numpy scipy opencv-python-headless`; install Chromium using Playwright, and install FFmpeg. Bootstrap pinned sources with `python motion_hub/hub.py bootstrap`.
Run `bash motion_hub/productions/008-rain-v1/build.sh` from the repo. Existing narration is reused. Missing narration uses the established project 068 entry; network access to Microsoft is needed. The generated SRT drives the timing JSON; this v1 uses the committed verified sentence times. New synthesis timing must be checked before rendering.
Fonts are local and OFL. Noto Sans TC is subset to the actual film characters; Inter comes from the pinned Huashu font bundle.
Technical verification is separate from film_gate, subjective listening, independent scoring, and user acceptance. Read CHECKPOINT.md for actual current status. No Actions run is claimed for this local film.
