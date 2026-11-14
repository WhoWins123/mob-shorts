import os
from functools import lru_cache

from PIL import ImageFont

FONT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "Poppins-Bold.ttf")


@lru_cache(maxsize=64)
def font(size: int):
    return ImageFont.truetype(FONT, max(8, size))


def wrap(text, f, max_width):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = (line + " " + w).strip()
        if f.getlength(test) <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines
