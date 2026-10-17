# Current task: gum packaging, official style 4

- User request: complete roughly 80-second Traditional Chinese 9:16 film, 1080x1920, official numbered style 4, existing 068 narration. Do not repeat material generation.
- Working branch: `render/gum-style4-80s`, based on main `9092822`.
- Prepared job: `handdraw/prepared/gum-style4`; catalog topic: `口香糖包裝的鋸齒邊`.
- Official unchanged engine commit: `5206ec0d17f9b353e400b64b9c51ad69e721e02a`.
- Narration: `zh-TW-HsiaoChenNeural`, +20%, +5Hz; measured 78.550204 seconds. Full text SHA256: `58bbd6b246a0800976e7c8c725ab070a4371170a7b75c82b3eea6f6694ff8817`.
- Seven real scene images created and reviewed. Source-aligned masks added for orange question tile / heat annotations. All seven passed the official tracer using their actual semantic masks.
- Eighteen real Edge sentence cues fit a single subtitle layer, at most two lines. No interpolated character timing.
- Preview workflow SUCCESS: https://github.com/dsf430-stack/short-video-factory/actions/runs/38991483069 . Diagnostics artifact `12084819950` contains actual 12-second MP4. Reviewed decoded page progression and five consecutive fill-stage frames; no subtitle/pen overlap in inspected frames. Preview shown to user.
- First full render SUCCESS: https://github.com/dsf430-stack/short-video-factory/actions/runs/38991764459 . 79.966667 seconds, H.264/AAC, 1080x1920 at 30fps. Actual film SHA256 `bd821a267dbb87ea3cb7e1963cf4ac9752a1f21e85ca14832c5ce93a6c1a8451`. Downloaded, full decoded, all seven pages and ending inspected. First full film shown to user.
- Layout revision SUCCESS: https://github.com/dsf430-stack/short-video-factory/actions/runs/38992266611 . Only moves the final heading inside its frame (`label_x=245`) and puts handwritten labels above source paper fill (`z=40`). Images, narration, subtitles and durations stay identical. Final v2 fully decodes, has same 79.966667s duration and identical decoded narration PCM to v1. Final SHA256: `a45443e7426354b0d047d460c1cf4f15eccc1ae7a16a6e170cf2aceb87ad07bc`. Viewed all seven v2 page-completion frames and full-size ending; heading conflict fixed.
- User-visible MP4 identity: `libfile_c5dc35e09e8c819192fae4fc7a9e7fca`, filename `Gum_Wrapper_Style04_068_80s.mp4`, current version 1. Successfully replaced with corrected v2 after QA, preserving the same file identity.
- Runtime label layout is authoritative in story.json; design.json records the art-planning stage.
- Final SHA-bound review is committed under handdraw/final-reviews/. Official cached finalization SUCCESS: https://github.com/dsf430-stack/short-video-factory/actions/runs/38992753059 . Final receipt status SUCCESS and SHA match the delivered v2. MP4 is saved (Library file version 1) and ready for user acceptance; do not regenerate images, voice or the completed film.
- Future invocation: existing sweety-handdraw-068.yml, topic `口香糖包裝的鋸齒邊`, seconds `80`.
- Audio subjective listening: UNCERTAIN. Do not claim naturalness or full human listening. Default no background music.
- Main has not been changed by this job; all new work is on the branch above.
