#!/usr/bin/env python3
"""Render a moving, hand-drawn-style vertical history explainer from verified 068 audio."""
import argparse
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 540, 960, 30
STATES = ["韓", "趙", "魏", "楚", "燕", "齊"]
CONQUEST = ["韓", "趙", "魏", "楚", "燕", "齊"]
POSITIONS = [(272, 390), (355, 290), (355, 430), (315, 590), (430, 235), (455, 490)]
INK = (47, 38, 30)
QIN = (180, 52, 35)
PAPER = (244, 231, 200)


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=nw=1:nk=1", str(path)]))


def font(size):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/msjh.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size, index=0)
    return ImageFont.load_default()


def eased(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def hand_line(draw, points, amount=1.0, width=3, fill=INK):
    # Segmented strokes intentionally expose the drawing progress instead of fading a static image.
    length = len(points) - 1
    whole = int(length * amount)
    fraction = length * amount - whole
    for index in range(whole):
        draw.line([points[index], points[index + 1]], fill=fill, width=width)
    if whole < length:
        x1, y1 = points[whole]
        x2, y2 = points[whole + 1]
        draw.line([(x1, y1), (x1 + (x2 - x1) * fraction, y1 + (y2 - y1) * fraction)],
                  fill=fill, width=width)


def label(draw, text, y, size=42, fill=INK):
    f = font(size)
    box = draw.textbbox((0, 0), text, font=f)
    draw.text(((W - (box[2] - box[0])) / 2, y), text, font=f, fill=fill)


def scene_index(t, total):
    # Intro, strength, strategy, six conquests, conclusion: all durations derive from real audio.
    stops = [0.16, 0.32, 0.46, 0.56, 0.64, 0.72, 0.80, 0.88, 1.0]
    ratio = t / total
    for i, stop in enumerate(stops):
        if ratio < stop:
            start = 0 if i == 0 else stops[i - 1]
            return i, (ratio - start) / (stop - start)
    return len(stops) - 1, 1.0


def draw_frame(t, total):
    image = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(image)
    # Moving paper grain and border strokes give the otherwise clean timeline a physical sketchbook texture.
    phase = int(t * FPS)
    for y in range(25 + phase % 7, H, 42):
        draw.line([(18, y), (W - 18, y - 2)], fill=(231, 216, 180), width=1)
    hand_line(draw, [(22, 22), (W - 22, 22), (W - 22, H - 22), (22, H - 22), (22, 22)], 1, 2, (116, 94, 70))
    scene, p = scene_index(t, total)
    label(draw, "秦始皇如何統一六國", 54, 36, QIN)
    draw.line([(75, 108), (W - 75, 108)], fill=QIN, width=2)
    if scene == 0:
        label(draw, "十年，改寫天下", 160, 33)
        for i, (name, pos) in enumerate(zip(["秦"] + STATES, [(145, 450)] + POSITIONS)):
            radius = 42 + int(5 * math.sin(t * 2 + i))
            draw.ellipse((pos[0] - radius, pos[1] - radius, pos[0] + radius, pos[1] + radius),
                         outline=QIN if name == "秦" else INK, width=3)
            label_font = font(30)
            draw.text((pos[0] - 15, pos[1] - 20), name, font=label_font,
                      fill=QIN if name == "秦" else INK)
        hand_line(draw, [(187, 450), (222, 430), (245, 410), (270, 390)], eased(p), 4, QIN)
    elif scene == 1:
        label(draw, "制度，變成國力", 160, 33)
        icons = [(120, 360, "變法"), (270, 360, "糧食"), (420, 360, "軍功")]
        for x, y, text in icons:
            progress = eased(min(1, p * 1.8))
            hand_line(draw, [(x - 48, y + 48), (x - 48, y - 48), (x + 48, y - 48), (x + 48, y + 48), (x - 48, y + 48)], progress, 3)
            draw.text((x - 28, y - 15), text, font=font(24), fill=INK)
        label(draw, "徵兵・收稅・補給", 540, 29, QIN)
    elif scene == 2:
        label(draw, "遠交近攻", 160, 40, QIN)
        center = (170, 465)
        draw.ellipse((center[0]-55, center[1]-55, center[0]+55, center[1]+55), outline=QIN, width=4)
        draw.text((center[0]-18, center[1]-22), "秦", font=font(35), fill=QIN)
        for i, pos in enumerate(POSITIONS):
            hand_line(draw, [center, pos], eased((p * 1.6) - i * .11), 3, QIN)
            draw.ellipse((pos[0]-28, pos[1]-28, pos[0]+28, pos[1]+28), outline=INK, width=2)
            draw.text((pos[0]-14, pos[1]-17), STATES[i], font=font(25), fill=INK)
    elif 3 <= scene <= 8:
        conquered = scene - 3
        target = CONQUEST[conquered]
        label(draw, f"第 {conquered + 1} 國：{target}", 155, 39, QIN)
        for i, (name, pos) in enumerate(zip(STATES, POSITIONS)):
            done = i < conquered
            active = name == target
            color = QIN if done or active else INK
            r = 47 if active else 38
            draw.ellipse((pos[0]-r, pos[1]-r, pos[0]+r, pos[1]+r), outline=color, width=4 if active else 2)
            draw.text((pos[0]-17, pos[1]-22), name, font=font(32), fill=color)
            if done:
                draw.line([(pos[0]-22, pos[1]), (pos[0]-5, pos[1]+18), (pos[0]+27, pos[1]-23)], fill=QIN, width=4)
        target_pos = POSITIONS[conquered]
        hand_line(draw, [(112, 500), (185, 475), (target_pos[0], target_pos[1])], eased(p), 5, QIN)
        draw.ellipse((72, 457, 152, 537), outline=QIN, width=4)
        draw.text((93, 475), "秦", font=font(30), fill=QIN)
        notes = ["先取最弱", "長平後受創", "引水灌城", "大國亦失守", "刺秦後反擊", "孤立而降"]
        label(draw, notes[conquered], 680, 28)
    else:
        label(draw, "天下歸一", 160, 44, QIN)
        for i, name in enumerate(["郡縣", "文字", "度量衡", "道路"]):
            angle = (t * .65 + i * math.pi / 2)
            x, y = 270 + int(math.cos(angle) * 145), 470 + int(math.sin(angle) * 145)
            hand_line(draw, [(270, 470), (x, y)], eased(p), 3, QIN)
            draw.ellipse((x-42, y-30, x+42, y+30), outline=INK, width=2)
            draw.text((x-27, y-15), name, font=font(20), fill=INK)
        draw.ellipse((220, 420, 320, 520), outline=QIN, width=5)
        draw.text((242, 442), "秦", font=font(40), fill=QIN)
        label(draw, "制度・後勤・外交・時間", 720, 27)
    draw.rectangle((45, 875, W - 45, 885), fill=(218, 195, 150))
    draw.rectangle((45, 875, 45 + (W - 90) * (t / total), 885), fill=QIN)
    return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preview-seconds", type=float, default=0)
    args = parser.parse_args()
    total = duration(args.audio)
    if total <= 1:
        raise RuntimeError("Narration is too short")
    render_seconds = min(total, args.preview_seconds) if args.preview_seconds else total
    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0", "-i", str(args.audio),
               "-filter:v", "scale=1080:1920:flags=lanczos", "-map", "0:v:0", "-map", "1:a:0",
               "-t", str(render_seconds), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
               str(args.output)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for frame in range(math.ceil(render_seconds * FPS)):
            process.stdin.write(draw_frame(frame / FPS, total).tobytes())
        process.stdin.close()
        if process.wait():
            raise RuntimeError("ffmpeg video encoding failed")
    except BaseException:
        process.stdin.close()
        process.terminate()
        process.wait()
        raise
    run(["ffmpeg", "-v", "error", "-xerror", "-i", str(args.output), "-f", "null", "-"])
    report = {"technical_status": "SUCCESS", "format": "1080x1920, 30fps, H.264/AAC",
              "duration_seconds": duration(args.output), "motion": "per-frame sketch strokes, map paths and animated state transitions"}
    args.output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

