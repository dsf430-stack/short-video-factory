"""Archival-photo flipbook mode, reusing the established sweety FFmpeg encoder."""
from pathlib import Path
import argparse
import bisect
import hashlib
import json
import math
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_srt(path):
    def seconds(value):
        h, m, s = value.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    cues = []
    for block in Path(path).read_text().strip().split('\n\n'):
        lines = block.splitlines()
        a, b = lines[1].split(' --> ')
        cues.append({'start': seconds(a), 'end': seconds(b), 'text': ''.join(lines[2:])})
    if not cues or any(c['end'] <= c['start'] for c in cues):
        raise ValueError('Real speech timestamps are required')
    return cues


def wrap(text, font, max_width):
    lines, current = [], ''
    for char in text:
        if current and font.getlength(current + char) > max_width:
            lines.append(current)
            current = ''
        current += char
    if current:
        lines.append(current)
    return lines


def perspective_coefficients(dst, src):
    matrix, values = [], []
    for (x, y), (u, v) in zip(dst, src):
        matrix.extend([[x, y, 1, 0, 0, 0, -u*x, -u*y],
                       [0, 0, 0, x, y, 1, -v*x, -v*y]])
        values.extend([u, v])
    return np.linalg.solve(np.array(matrix), np.array(values)).tolist()


class FlipbookRenderer:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.work = self.root / 'work'
        self.output = self.root / 'outputs'
        self.work.mkdir(exist_ok=True)
        self.output.mkdir(exist_ok=True)
        self.manifest = json.loads((self.root / 'job.json').read_text())
        self.width, self.height, self.fps = 1280, 720, 30
        self.font_path = self.root / 'inputs/NotoSansCJK-Regular.ttc'
        self.fonts = {size: ImageFont.truetype(str(self.font_path), size, index=3)
                      for size in [16, 17, 19, 22, 26, 32, 38, 42]}
        self.cues = read_srt(self.root / 'inputs/preview.srt')
        self.voice_duration = float(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(self.root / 'inputs/preview.mp3')]))
        self.offset = .35
        self.duration = self.offset + self.voice_duration + .45
        self.timeline = {'duration': self.duration}
        if len(self.manifest['pages']) != 2:
            raise ValueError('This representative preview requires exactly two pages; never silently omit full-book pages')
        for page in self.manifest['pages']:
            if len(page['photos']) < 3 or len(set(page['photos'])) != len(page['photos']):
                raise ValueError('Each page must contain at least three distinct photographs')
        self.turn_at = self.offset + self.cues[1]['start']
        self.turn_length = .95
        self.pages = [self.compose_page(p, i) for i, p in enumerate(self.manifest['pages'])]
        self.background = self.make_background()

    def text(self, draw, position, text, size, color='#302d25'):
        draw.text(position, text, font=self.fonts[size], fill=color)

    def make_background(self):
        image = Image.new('RGB', (self.width, self.height), '#253830')
        d = ImageDraw.Draw(image)
        for y in range(0, self.height, 4):
            c = 47 + int(3*math.sin(y*.028))
            d.line((0, y, self.width, y), fill=(32, c, 40), width=1)
        d.rounded_rectangle((70, 65, 1230, 635), radius=7, fill='#15251e')
        d.rounded_rectangle((60, 52, 1210, 626), radius=6, fill='#6d493c')
        d.rectangle((71, 64, 1204, 620), fill='#d6c8ae')
        for y in range(72, 620, 5):
            d.line((73, y, 1206, y), fill='#bdb098', width=1)
        return image

    def compose_page(self, page, number):
        image = Image.new('RGB', (1128, 550), '#f8f0df')
        d = ImageDraw.Draw(image)
        d.rectangle((0, 0, 15, 550), fill='#e0d2b7')
        d.line((28, 0, 28, 550), fill='#c8b897', width=2)
        for y in [90, 240, 400]:
            d.ellipse((6, y, 20, y+14), fill='#8e7a5e')
        self.text(d, (54, 25), '島嶼工作相簿  /  TAIWAN', 17, '#82745e')
        self.text(d, (54, 59), page['title'], 42)
        self.text(d, (54, 117), page['subtitle'], 22, '#70614e')
        for k, photo_id in enumerate(page['photos']):
            photo = self.manifest['photos'][str(photo_id)]
            path = self.root / 'inputs' / photo['file']
            if digest(path) != photo['sha256']:
                raise ValueError('Photograph changed after download: ' + str(photo_id))
            src = Image.open(path).convert('RGB')
            x, y, w, h = 54 + k*350, 170, 326, 214
            d.rectangle((x-5, y-5, x+w+5, y+h+6), fill='#fcfaf4', outline='#a6957b', width=1)
            # Fit the entire original photograph: no fabricated detail, recoloring or content crop.
            fitted = ImageOps.contain(src, (w, h), Image.Resampling.LANCZOS)
            image.paste(fitted, (x+(w-fitted.width)//2, y+(h-fitted.height)//2))
            self.text(d, (x, 398), photo['label'], 22)
            self.text(d, (x, 432), photo['date'], 17, '#796c5a')
            self.text(d, (x, 458), photo['credit_short'], 16, '#796c5a')
        self.text(d, (54, 501), page['note'], 17, '#796c5a')
        self.text(d, (1067, 501), f'{number+1:02d}', 19, '#796c5a')
        return image

    def turn_frame(self, progress):
        frame = self.background.copy().convert('RGBA')
        frame.alpha_composite(self.pages[1].convert('RGBA'), (76, 63))
        angle = math.pi * progress
        width, height = self.pages[0].size
        hinge_x, top = 76, 63
        projected = width * math.cos(angle)
        if abs(projected) < 3:
            projected = 3 if projected >= 0 else -3
        lift = 48 * math.sin(angle)
        if progress < .5:
            sheet = self.pages[0].convert('RGBA')
        else:
            sheet = Image.new('RGBA', (width, height), '#eee3cc')
            sd = ImageDraw.Draw(sheet)
            sd.line((width-18, 0, width-18, height), fill='#c9b797', width=3)
        brightness = .96 - .25*math.sin(angle)
        sheet = ImageEnhance.Brightness(sheet).enhance(brightness)
        dst = [(hinge_x, top), (hinge_x+projected, top+lift),
               (hinge_x+projected, top+height-lift), (hinge_x, top+height)]
        src = [(0, 0), (width, 0), (width, height), (0, height)]
        coeff = perspective_coefficients(dst, src)
        plane = sheet.transform((self.width, self.height), Image.Transform.PERSPECTIVE,
                                coeff, Image.Resampling.BICUBIC)
        shadow = Image.new('RGBA', frame.size)
        sd = ImageDraw.Draw(shadow)
        edge = hinge_x + projected
        if progress < .5:
            for i in range(22):
                sd.line((edge+i, top+lift+9, edge+i, top+height-lift+9),
                        fill=(25, 20, 14, int((22-i)*2)))
        frame.alpha_composite(shadow)
        frame.alpha_composite(plane)
        # The highlighted curved fore-edge follows the projected page, not a wipe.
        d = ImageDraw.Draw(frame)
        d.line((edge, top+lift, edge, top+height-lift), fill='#cab894', width=2)
        return frame.convert('RGB')

    def frame(self, time):
        if self.turn_at <= time < self.turn_at+self.turn_length:
            progress = (time-self.turn_at)/self.turn_length
            progress = progress*progress*(3-2*progress)
            frame = self.turn_frame(progress)
        else:
            page = 0 if time < self.turn_at else 1
            frame = self.background.copy()
            frame.paste(self.pages[page], (76, 63))
        d = ImageDraw.Draw(frame)
        cue = next((c for c in self.cues if c['start']+self.offset <= time < c['end']+self.offset), None)
        if cue:
            font = self.fonts[32]
            lines = wrap(cue['text'], font, 1130)
            if len(lines) > 2:
                raise ValueError('Subtitle exceeds two readable lines')
            for idx, line in enumerate(lines):
                width = font.getlength(line)
                d.text(((self.width-width)/2, 626+idx*40), line, font=font, fill='white',
                       stroke_width=2, stroke_fill='#19231e')
        return frame

    def audio(self):
        music = self.root / 'inputs/music.wav'
        sr = 48000
        n = math.ceil(self.duration*sr)
        samples = np.zeros(n)
        for start, frequency in [(0, 196), (2.5, 261.6256), (5, 293.6648), (7.5, 392), (10, 329.6276), (12.5, 261.6256)]:
            k = round(start*sr)
            if k >= n:
                continue
            t = np.arange(n-k)/sr
            envelope = (1-np.exp(-t*30))*np.exp(-t*1.3)
            tone = sum(np.sin(2*math.pi*frequency*m*t)*np.exp(-t*m*.25)/(m*m) for m in range(1, 6))
            samples[k:] += .12*tone*envelope
        samples *= np.minimum(1, (n-np.arange(n))/sr/.7)
        with wave.open(str(music), 'wb') as stream:
            stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(sr)
            stream.writeframes(np.clip(samples*32767, -32768, 32767).astype('<i2').tobytes())
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(self.root/'inputs/preview.mp3'),
                        '-i', str(music), '-filter_complex',
                        f'[0:a]adelay=350:all=1,apad,atrim=duration={self.duration}[voice];'
                        '[1:a]volume=0.045[bed];[voice][bed]amix=inputs=2:normalize=0:duration=first,'
                        'alimiter=limit=0.891:level=false:latency=true[out]', '-map', '[out]',
                        '-ar', str(sr), '-ac', '2', str(self.work/'mix.wav')], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('job', type=Path)
    parser.add_argument('--sweety-scripts', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.sweety_scripts.resolve()))
    from video_renderer import encode
    renderer = FlipbookRenderer(args.job)
    renderer.audio()
    for idx, page in enumerate(renderer.pages):
        page.save(renderer.work/f'page-{idx+1:02d}.png')
    for idx, t in enumerate([0, renderer.turn_at, renderer.turn_at+.22,
                             renderer.turn_at+.47, renderer.turn_at+.72,
                             renderer.turn_at+.96, renderer.duration-.5]):
        renderer.frame(t).save(renderer.work/f'review-{idx:02d}.jpg')
    output = renderer.output/'台灣經濟發展_翻頁舊照試片.mp4'
    encode(renderer, output)
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-f', 'null', '-'], check=True)
    report = {'status': 'SUCCESS_TECHNICAL_REVIEW_REQUIRED', 'duration': renderer.duration,
              'pages': len(renderer.pages), 'photos_per_page': [len(p['photos']) for p in renderer.manifest['pages']],
              'distinct_photographs': len(renderer.manifest['photos']), 'full_decode': True,
              'actual_page_turn_seconds': [renderer.turn_at, renderer.turn_at+renderer.turn_length],
              'voice': '068 HsiaoChenNeural +20% +5Hz', 'subjective_listening': 'UNCERTAIN',
              'auto_ducking': False, 'music_gain': .045, 'sha256': digest(output)}
    (renderer.output/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
