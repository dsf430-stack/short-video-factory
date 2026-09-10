# Kids English MVP

The MVP renders a self-contained 10-second, 9:16 English vocabulary lesson with:

- a child-friendly animated mascot and timed teaching captions;
- English narration plus quiet background tone;
- H.264/AAC MP4 output compatible with phones and social platforms;
- an automated `ffprobe` quality gate.

## Render and verify POTATO

```bash
npm run kids:potato
npm run kids:verify
```

Output: `dist/kids-english/POTATO.mp4`

The renderer first uses the project's `ffmpeg-static` dependency. If dependencies have not been installed, it automatically uses an `ffmpeg` executable available on `PATH`.
