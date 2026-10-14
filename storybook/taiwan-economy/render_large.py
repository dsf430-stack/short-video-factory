from pathlib import Path
import sys
import subprocess
import json
from flipbook_renderer import FlipbookRenderer, digest

root = Path(__file__).resolve().parent
sys.path.insert(0, '/workspace/scratch/9eddb35262ad/.agents/skills/sweety-handdraw-video/scripts')
from video_renderer import encode
renderer = FlipbookRenderer(root)
assert (root/'work/mix.wav').is_file()
target = root/'outputs/台灣經濟發展_翻頁大圖試片.mp4'
encode(renderer, target)
subprocess.run(['ffmpeg', '-v', 'error', '-i', str(target), '-f', 'null', '-'], check=True)
def audio_md5(path):
    return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a', '-c', 'copy', '-f', 'md5', '-']).decode().strip()
assert audio_md5(target) == audio_md5(root/'outputs/台灣經濟發展_翻頁舊照試片.mp4')
for k, t in enumerate([1.0, 2.7, 4.3, 5.82, 7.45, 9.45, 11.4]):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(target), '-frames:v', '1', str(root/'work'/f'large-{k:02d}.jpg')], check=True)
(root/'outputs/large_verification.json').write_text(json.dumps({'status':'SUCCESS_TECHNICAL_REVIEW_REQUIRED','duration':renderer.duration,'pages':2,'photos_per_page':[3,3],'enlarged_photo_fit_box':[1200,536],'previous_photo_fit_box':[326,214],'narration_and_music_stream_identical':True,'full_decode':True,'sha256':digest(target),'subjective_listening':'UNCERTAIN'},ensure_ascii=False,indent=2))
print(target)
