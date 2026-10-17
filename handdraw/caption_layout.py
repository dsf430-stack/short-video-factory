"""Choose an official caption width without changing speech or subtitle text."""
import unicodedata


def wrap_lines(text, measure, limit):
    lines, current = [], ''
    for character in text:
        if character == '\n' or (current and measure(current + character) > limit):
            lines.append(current)
            current = ''
        if character != '\n':
            current += character
    if current:
        lines.append(current)
    return lines


def choose_caption_width(texts, measure, canvas_width=1080, stroke=2, max_lines=2):
    texts = list(texts)
    for percent in range(90, 75, -1):
        ratio = percent / 100
        lines = [wrap_lines(text, measure, int(canvas_width * ratio) - 16 - stroke * 2)
                 for text in texts]
        if all(0 < len(rows) <= max_lines and
               all(row.strip() and not unicodedata.category(row.lstrip()[0]).startswith('P')
                   for row in rows[1:]) for rows in lines):
            return ratio
    raise ValueError('CAPTION_LAYOUT_REQUIRED: split long editorial sentences at measured speech boundaries; keep the voice and subtitle text intact')
