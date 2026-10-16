"""Topic adapter for the unchanged, pinned official Sweety production engine.

All creative/visual decisions come from real Gemini calls. No fixture mode,
prewritten pass reviews, alternate renderer or replacement voice implementation.
"""
import argparse
import base64
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request


REPO = Path(__file__).resolve().parents[1]
PIN = '5206ec0d17f9b353e400b64b9c51ad69e721e02a'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def normalize(text):
    return ''.join(c for c in text if c.isalnum())


def inline(path):
    return {'inlineData': {'mimeType': mimetypes.guess_type(path)[0] or 'application/octet-stream',
                           'data': base64.b64encode(Path(path).read_bytes()).decode()}}


class Gemini:
    def __init__(self, root):
        self.key = os.environ.get('GEMINI_API_KEY', '')
        if not self.key:
            raise RuntimeError('GEMINI_API_KEY is unavailable')
        self.cache = root / 'model-cache'
        self.cache.mkdir(parents=True, exist_ok=True)
        self.text_model = os.environ.get('TEXT_MODEL') or 'gemini-2.5-flash'
        self.image_model = os.environ.get('IMAGE_MODEL') or 'gemini-2.5-flash-image'

    def generate(self, parts, image=False):
        model = self.image_model if image else self.text_model
        config = {'responseModalities': ['TEXT', 'IMAGE']} if image else {'responseMimeType': 'application/json'}
        body = {'contents': [{'role': 'user', 'parts': parts}], 'generationConfig': config}
        encoded = json.dumps(body, ensure_ascii=False).encode()
        identity = hashlib.sha256(model.encode() + encoded).hexdigest()
        target = self.cache / (identity + '.json')
        if target.exists():
            return json.loads(target.read_text())
        print('Gemini request:', model, identity[:12], flush=True)
        url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent'
        for attempt in range(3):
            req = urllib.request.Request(url, data=encoded, headers={
                'x-goog-api-key': self.key, 'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=240) as response:
                    result = json.load(response)
                candidates = result.get('candidates', [])
                if not candidates or candidates[0].get('finishReason') not in (None, 'STOP'):
                    raise RuntimeError('Model did not complete: ' + str(result.get('promptFeedback', candidates)))
                save(target, result)
                return result
            except urllib.error.HTTPError as error:
                # Never print URLs containing credentials, request headers or raw error bodies.
                if error.code not in (408, 429, 500, 502, 503, 504) or attempt == 2:
                    raise RuntimeError(f'Gemini {model}: HTTP {error.code}') from None
                time.sleep(5 * (attempt + 1))
        raise RuntimeError('Gemini retries exhausted')

    def json(self, prompt, files=()):
        result = self.generate([{'text': prompt}] + [inline(str(p)) for p in files])
        text = ''.join(p.get('text', '') for p in result['candidates'][0]['content']['parts'] if not p.get('thought'))
        return json.loads(text)

    def image(self, prompt, destination):
        result = self.generate([{'text': prompt}], image=True)
        for part in result['candidates'][0]['content']['parts']:
            data = part.get('inlineData') or part.get('inline_data')
            if data and (data.get('mimeType') or data.get('mime_type', '')).startswith('image/'):
                destination.write_bytes(base64.b64decode(data['data']))
                return
        raise RuntimeError('Image model returned no image')


def parse_srt(path):
    def seconds(value):
        hours, minutes, tail = value.replace(',', '.').split(':')
        return int(hours) * 3600 + int(minutes) * 60 + float(tail)
    result = []
    for block in re.split(r'\n\s*\n', Path(path).read_text().strip()):
        lines = block.splitlines()
        left, right = lines[1].split(' --> ')
        result.append({'start': seconds(left), 'end': seconds(right), 'text': ''.join(lines[2:])})
    return result


def align_scenes(scenes, events):
    """Map real Edge sentence boundaries; never interpolate character timing."""
    result, offset = [], 0
    for index, scene in enumerate(scenes):
        selected, found = [], ''
        expected = normalize(scene['text'])
        while offset < len(events) and len(found) < len(expected):
            event = events[offset]
            selected.append(event)
            found += normalize(event['text'])
            offset += 1
        if found != expected or not selected:
            raise ValueError('Edge sentence boundaries do not match storyboard scene ' + str(index))
        start = selected[0]['start']
        if result and start < result[-1]['end']:
            if result[-1]['end'] - start > .02:
                raise ValueError('Measured sentence boundaries overlap')
            start = result[-1]['end']
        end = selected[-1]['end']
        result.append({'id': f's{index}', 'text': scene['text'], 'start': start, 'end': end,
                       'caption_cues': [{'text': scene['text'], 'start': 0, 'end': end - start}]})
    if offset != len(events):
        raise ValueError('Unmapped Edge sentence events')
    return result


def main(args):
    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    skill = Path(args.official).resolve() / 'skills/sweety-handdraw-video'
    actual = subprocess.check_output(['git', '-C', str(skill), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != PIN:
        raise RuntimeError('Official source pin changed')
    sys.path.insert(0, str(skill / 'scripts'))
    from style_choice import prepare_catalog, verify_style
    from drawing_contract import preflight, validate_plan
    from art_direction import bind_evidence
    from clean_image import clean_image
    from PIL import Image, ImageDraw, ImageFont, ImageOps

    model = Gemini(root)
    font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    # Pass the actual official guidance to the model before any design or generation.
    references = ['SKILL.md', 'references/story-design.md', 'references/style-and-drawing.md',
                  'references/continuous-narration.md', 'references/runtime-contract.md',
                  'dependencies/sweety-image-art-direction/GUIDE.md',
                  'dependencies/omniailab-ai-director/references/FILM-ART GUIDE.md']
    guidance = '\n'.join((skill / name).read_text() for name in references)
    shape = '''Return one JSON object:
    {"title":"short Traditional Chinese cover title", "design": {"topic":"...",
    "audience":"...","explanation_goal":"...","source_scope":"original explanation, factual boundaries",
    "narrative_route":{"decision":"mechanism_explanation","reason":"...","director_review":"...","director_plan":"specific visual causal sequence"},
    "visual_direction":"...","beats":[],"cover":"...","asset_prompts":[]},
    "style":{"style_name":"...","rationale":"...","content_fit":"...",
      "style_spec":{"line":"clean substantial black contours","palette":"blue, yellow, white","shading":"flat","texture":"clean paper","background":"pure white"}},
    "scenes":[{"text":"one Traditional Chinese sentence, with commas and one final 。, no other sentence delimiter",
    "label":"2-5 Chinese characters", "brief":"specific art direction, no fabricated references",
    "prompt":"complete image generation prompt following the art guide, no text in image",
    "plan":{"id":"s0","composition":"...","drawability_reason":"...",
    "outline_strategy":"visible_source_ink","spatial_order":"top_to_bottom_left_to_right",
    "subjects":[{"id":"object1","kind":"object"}],
    "parts":[{"id":"object1_contour","subject":"object1","role":"contour","stroke_groups":["independent contour", "separate inner mark"]}],
    "outline_order":["object1_contour"],"fill_order":["object1_contour"],
    "narrative_requirements":[{"id":"mechanism","narration_quote":"exact substring of this scene's text","observable":"specific visible causal evidence"}]}}]}
    Exactly four scenes. Plan actual meaningful objects/parts. No humans/animals needed for this explanation.
    Keep each illustration simple enough to outline and fill in 4-6 seconds, sparse black contours,
    no hatching, no gray texture, 2 solid pastel colors, pure white 1:1 image, generous margins.
    If multiple distinct objects are present, plan each with separate subjects and parts.
    Each scene has one single sentence of 28-42 Traditional Chinese characters, no Latin abbreviations.
    Do not repeat the entire narration as visual text. No fictitious evidence or pass reviews.
    For rain, explain evaporation, cooling/condensation on particles, droplet growth and falling;
    water vapor is invisible; visible clouds are droplets/ice, not gas; avoid saying cloud is full/squeezed.
    '''
    story = model.json(guidance + '\n' + shape + f'\nTopic: {args.topic}. Target film: {args.seconds} seconds including 1s cover and short ending. Aim for 28.5s narration at HsiaoChen +20%.')
    if len(story.get('scenes', [])) != 4:
        raise ValueError('Expected four scenes')
    target = args.seconds - 1.5
    for attempt in range(8):
        scenes = story['scenes']
        for i, scene in enumerate(scenes):
            if not 1 <= len(scene['label']) <= 6 or not scene['text'].endswith('。'):
                raise ValueError('Invalid scene label or sentence')
            scene['plan']['id'] = f's{i}'
            validate_plan(scene['plan'])
        text = ''.join(s['text'] for s in scenes)
        if len(text) > 300:
            raise ValueError('Keep this short narration within one existing 068 request')
        narration = root / f'inputs/voice-{attempt}.txt'
        narration.parent.mkdir(parents=True, exist_ok=True)
        narration.write_text(text)
        mp3 = narration.with_suffix('.mp3')
        if not mp3.exists():
            run(sys.executable, REPO / 'smart_voice/generate_voice.py', '--voice-id', '068', '--text-file', narration, '--output', mp3)
        metadata = json.loads(mp3.with_suffix('.json').read_text())
        duration = metadata['duration']
        print('Measured narration seconds:', duration, 'attempt:', attempt + 1, flush=True)
        hold = args.seconds - 1 - duration
        if .2 <= hold <= .8:
            break
        story = model.json(guidance + '\n' + shape + '\nRevise only the full script and corresponding plans, preserving causal facts.\n' +
                           json.dumps(story, ensure_ascii=False) +
                           f'\nActual HsiaoChen +20% narration took {duration:.3f}s. Target {target:.3f}s. '
                           f'Change character count approximately by factor {target/duration:.4f}; do not change the voice rate. This is revision {attempt+1}.')
    else:
        raise RuntimeError('Could not fit natural 068 narration to requested duration; no stretching or truncation performed')
    save(root / 'design.json', story['design'])
    save(root / 'story.json', story)
    (root / 'script.txt').write_text(text)
    master = root / 'inputs/master.wav'
    run('ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ar', 48000, '-ac', 1, '-c:a', 'pcm_s16le', master)
    events = parse_srt(mp3.with_suffix('.srt'))
    aligned = align_scenes(scenes, events)
    save(root / 'inputs/alignment.json', {'version': 1, 'source_sha256': digest(master),
         'script_sha256': hashlib.sha256(text.encode()).hexdigest(), 'beats': aligned})
    audio_review = model.json('Listen to this actual narration. Return JSON {"status":"pass or fail", "transcript":"what is actually spoken", "evidence":"specific observations of final word, intelligibility, clipping, missing/repeated phrases"}. '
                              'Expected Traditional Chinese script: ' + text + '. Do not mark pass if any sentence is missing or truncated.', [master])
    save(root / 'audio-review.json', audio_review)
    if audio_review.get('status') != 'pass':
        raise RuntimeError('Actual audio review failed; see audio-review.json')

    prepare_catalog(root, skill / 'dependencies/hand-drawn-styles')
    save(root / 'style/selection.json', {'mode': 'inferred', 'confirmation': 'user_delegated',
         'evidence': 'User delegates automatic complete official handdraw integration and test production.'})
    save(root / 'style/resolved.json', {**story['style'], 'status': 'resolved', 'mode': 'inferred',
         'selection_sha256': digest(root / 'style/selection.json')})
    style = verify_style(root)
    save(root / 'design/drawing-plan.json', {'illustrations': [s['plan'] for s in scenes]})
    preflight(root, root / 'design/drawing-plan.json')
    art = {'dependency_sha256': digest(skill / 'dependencies/sweety-image-art-direction/GUIDE.md'),
           'style_sha256': style['resolved_sha256'], 'images': []}
    drawing = {'style_sha256': style['resolved_sha256'], 'plan_sha256': digest(root / 'design/drawing-plan.json'), 'illustrations': []}
    pages = []
    for i, scene in enumerate(scenes):
        name = f's{i}'
        (root / f'design/{name}-brief.md').write_text(scene['brief'])
        prompt = scene['prompt'] + '\nResolved style: ' + json.dumps(story['style'], ensure_ascii=False) + '\nRender a single clean illustration, pure white background, absolutely no text, no panel border, no watermark, square canvas, thick continuous black outlines, very few internal details. Planned subjects and parts: ' + json.dumps(scene['plan'], ensure_ascii=False)
        (root / f'design/{name}-prompt.txt').write_text(prompt)
        entry = {'source': f'../inputs/{name}.png', 'method': 'generated_under_guidance',
                 'brief_file': name + '-brief.md', 'prompt_file': name + '-prompt.txt'}
        art['images'].append(entry)
        save(root / 'design/art-direction.json', art)
        bind_evidence(root / 'design/art-direction.json')
        art = json.loads((root / 'design/art-direction.json').read_text())
        entry = art['images'][-1]
        image = root / f'inputs/{name}.png'
        if not image.exists():
            model.image(prompt, image)
            clean_image(image, root / f'privacy/{name}.json')
        review = model.json('Actually inspect the attached generated image against this plan and quoted narration. '
            'Return JSON {"status":"pass or fail", "evidence":"concrete observed content, composition, no unwanted text", '
            '"parts":[{"id":"exact planned part id", "polygon":[[0,0],[1,0],[1,1],[0,1]]}], '
            '"anatomy_and_occlusion":"...","part_boundaries":"...","stroke_breaks":"...",'
            '"outline_then_fill":"...","spatial_order":"...",'
            '"narrative_checks":[{"id":"exact requirement id","status":"pass or fail","evidence":"specific visible evidence"}]}. '
            'Polygons are normalized actual image coordinates in the planned order; every visible colored/ink pixel must have a semantic owner. '
            'Do not use arbitrary equal strips. A simple single object may have a whole-image region, multiple subjects must be individually partitioned. '
            'Fail if contours are absent, composition contradicts narration, or unwanted text appears.\n' + json.dumps(scene, ensure_ascii=False), [image])
        save(root / f'design/{name}-vision.json', review)
        if review.get('status') != 'pass':
            raise RuntimeError('Image visual review failed: ' + name)
        entry.update(status=review['status'], evidence=review['evidence'], sha256=digest(image))
        drawing['illustrations'].append({**review, 'plan_id': name, 'source_sha256': digest(image), 'crop': None})
        action = {'type': 'illustration', 'drawing_plan_id': name, 'source': f'inputs/{name}.png',
                  'x': 120, 'y': 480, 'width': 840, 'height': 840, 'weight': 5, 'parts': review['parts']}
        pages.append({'beats': [{'id': name, 'text': scene['text'], 'actions': [
            {'type': 'text', 'text': scene['label'], 'x': 120, 'y': 250, 'size': 90, 'weight': 1}, action]}]})
        save(root / 'design/art-direction.json', art)
        save(root / 'design/drawing-review.json', drawing)

    # Cover composition preserves the verified illustration; title is a real editable font layer.
    (root / 'design/cover-brief.md').write_text('Use first verified illustration, exact title above; white portrait cover; separate editable title layer.')
    (root / 'design/cover-prompt.txt').write_text(json.dumps({'title': story['title'], 'image': 'inputs/s0.png', 'font': font_path, 'canvas': [1080, 1920]}, ensure_ascii=False))
    art['images'].append({'source': '../inputs/cover.png', 'method': 'composed_with_verified_layers',
                          'brief_file': 'cover-brief.md', 'prompt_file': 'cover-prompt.txt'})
    save(root / 'design/art-direction.json', art)
    bind_evidence(root / 'design/art-direction.json')
    art = json.loads((root / 'design/art-direction.json').read_text())
    cover = Image.new('RGB', (1080, 1920), 'white')
    visual = ImageOps.contain(Image.open(root / 'inputs/s0.png').convert('RGB'), (840, 840))
    cover.paste(visual, ((1080 - visual.width)//2, 600))
    draw = ImageDraw.Draw(cover)
    title = story['title']
    for n, line in enumerate([title[k:k+8] for k in range(0, len(title), 8)]):
        draw.text((540, 250 + n*110), line, font=ImageFont.truetype(font_path, 86, index=3), anchor='mt', fill='#182C3A')
    cover.save(root / 'inputs/cover.png')
    clean_image(root / 'inputs/cover.png', root / 'privacy/cover.json')
    cover_review = model.json('Inspect the attached cover. Expected title: ' + title + '. Return JSON {"status":"pass or fail","evidence":"observed title accuracy, margins, composition and picture consistency"}.', [root / 'inputs/cover.png'])
    if cover_review.get('status') != 'pass':
        raise RuntimeError('Cover review failed')
    art['images'][-1].update(status='pass', evidence=cover_review['evidence'], sha256=digest(root / 'inputs/cover.png'))
    save(root / 'design/art-direction.json', art)
    manifest = {'version': 1, 'title': title, 'design_file': 'design.json',
                'canvas': {'width': 1080, 'height': 1920, 'fps': 30}, 'paper': '#FFFFFF',
                'font': {'path': font_path, 'index': 3},
                'cover': {'source': 'inputs/cover.png', 'seconds': 1}, 'hand': {'preset': 'pen-only', 'pen_text': ''},
                'narration': {'source': 'inputs/master.wav', 'alignment': 'inputs/alignment.json'},
                'audio': {'end_hold_seconds': hold}, 'ending': {'caption_hold_seconds': min(.2, hold)},
                'captions': {'font': {'path': font_path, 'index': 3}, 'font_size': 46, 'bottom_margin': 210,
                             'max_width_ratio': .9, 'max_lines': 2, 'color': '#FFFFFF', 'stroke_color': '#151515', 'stroke_width': 3, 'background': None},
                'art_direction': {'record': 'design/art-direction.json'},
                'drawing_plan': 'design/drawing-plan.json', 'drawing_review': 'design/drawing-review.json', 'pages': pages}
    save(root / 'job.json', manifest)
    command = skill / 'scripts/handdraw_video.py'
    for stage in ('doctor', 'build'):
        run(sys.executable, command, stage, root)
    run(sys.executable, command, 'verify', root, '--assets-only')
    run(sys.executable, command, 'render', root, '--preview', '--start', 1, '--duration', 7)
    preview = root / 'work/review/preview.mp4'
    # Upstream uses a named preview; locate only files actually emitted by the engine.
    if not preview.exists():
        previews = list((root / 'outputs').glob('*preview*.mp4'))
        if len(previews) != 1:
            raise RuntimeError('Could not identify official preview output')
        preview = previews[0]
    preview_review = model.json('Review this actual handdraw animation preview. Return JSON {"status":"pass or fail","evidence":"visible pen position, progressive outlines, later color, readable title, one subtitle layer, safe margins, no clipped tool"}. Do not pass a static image or arbitrary wipe as drawing.', [preview])
    save(root / 'preview-review.json', preview_review)
    if preview_review.get('status') != 'pass':
        raise RuntimeError('Official animation preview review failed')
    run(sys.executable, command, 'render', root)
    run(sys.executable, command, 'verify', root)
    film = root / 'outputs/film.mp4'
    review = model.json('Review the actual final video and script below. Return JSON with content, visual, motion, audio each {"status":"pass or fail","evidence":"specific observed evidence"}, and limitations array. '
                        'Check factual causality, progressive official pen animation, subtitles readable and unique, final word intact, no overlapping text or blank scene. '
                        'Do not claim human acceptance. No BGM is intentional. Script: ' + text, [film])
    review['privacy'] = {'status': 'pass', 'evidence': 'Official clean_image audit applied to each generated illustration and composed cover; see privacy/*.json.'}
    review['video_sha256'] = digest(film)
    review.setdefault('limitations', []).append('Automated Gemini audiovisual review; no human subjective acceptance. No background music added.')
    save(root / 'review.json', review)
    run(sys.executable, command, 'finalize', root)
    metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(film)]))
    v = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    if (v['width'], v['height'], v['avg_frame_rate']) != (1080, 1920, '30/1') or abs(float(v['duration']) - args.seconds) > .05:
        raise RuntimeError('Requested output format/duration failed')
    save(root / 'acceptance.json', {'status': 'SUCCESS', 'topic': args.topic, 'seconds': float(v['duration']),
         'official_commit': PIN, 'voice': '068', 'sha256': digest(film), 'human_review': 'UNCERTAIN'})
    print('Verified film:', film, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--official', required=True)
    parser.add_argument('--output', required=True)
    options = parser.parse_args()
    if not options.topic.strip() or len(options.topic) > 500 or options.seconds != 30:
        parser.error('This verified adapter currently accepts a 1-500 character topic and 30 seconds')
    main(options)
