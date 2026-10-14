from pathlib import Path
import json
import subprocess
import wave
import numpy as np
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent
video = root/'outputs/台灣經濟發展_翻頁舊照試片.mp4'
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]))
streams = probe['streams']
assert len(streams) == 2 and {s['codec_type'] for s in streams} == {'video', 'audio'}
assert streams[0]['codec_name'] == 'h264' and streams[0]['pix_fmt'] == 'yuv420p'
assert streams[0]['width'] == 1280 and streams[0]['height'] == 720
assert streams[1]['codec_name'] == 'aac'
assert not any((root/'outputs').glob('*.srt'))
report = json.loads((root/'outputs/verification.json').read_text())
turn = report['actual_page_turn_seconds'][0]
frames = []
for k, t in enumerate([.5, 3.0, turn+.12, turn+.3, turn+.48, turn+.66, turn+.83, 9.0, 12.0]):
    path = root/'work'/f'decoded-{k:02d}.jpg'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(video), '-frames:v', '1', str(path)], check=True)
    image = Image.open(path).convert('RGB')
    assert np.asarray(image).mean() > 15
    frames.append(image)
sheet = Image.new('RGB', (1280, 390*5), '#e8e8e8')
draw = ImageDraw.Draw(sheet)
for k, image in enumerate(frames):
    sheet.paste(image.resize((640, 360)), (k%2*640, k//2*390))
    draw.text((k%2*640+12, k//2*390+364), f'Decoded {k}', fill='black')
sheet.save(root/'work/decoded-contact.jpg')
for name, src in [('source', root/'inputs/preview.mp3'), ('decoded', video)]:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-vn', '-ar', '48000', '-ac', '1', str(root/'work'/f'{name}.wav')], check=True)
with wave.open(str(root/'work/source.wav')) as w:
    source = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2')
with wave.open(str(root/'work/decoded.wav')) as w:
    decoded = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2')
start = round(.35*48000)
correlation = float(np.corrcoef(source, decoded[start:start+len(source)])[0, 1])
assert correlation > .995
result = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(video), '-af', 'loudnorm=I=-11:TP=-1:LRA=7:print_format=json', '-f', 'null', '-'], text=True, capture_output=True, check=True)
volume = json.loads(result.stderr[result.stderr.rfind('{'):])
report.update(video_streams=1, audio_streams=1, subtitle_streams=0, adjacent_subtitles=0,
              nonblack_frames=True, decoded_review_frames=len(frames),
              narration_correlation=correlation, loudness_measured=volume,
              visual_review='PENDING', motion_review='PENDING', subjective_listening='UNCERTAIN')
(root/'outputs/verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False))
