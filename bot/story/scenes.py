"""Simple cartoon backgrounds drawn with shapes (1080x1920). Characters stand on GROUND_Y."""
import math
import random
from functools import lru_cache

from PIL import Image, ImageDraw

W, H = 1080, 1920
GROUND_Y = 1380
OUT = (20, 20, 25)


def _grad(d, top, bottom, y0=0, y1=H):
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0)
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))


def _clouds(d, rng, n=4, color=(255, 255, 255)):
    for _ in range(n):
        x, y = rng.randint(-50, W), rng.randint(480, 820)
        for k in range(4):
            r = rng.randint(40, 70)
            d.ellipse([x + k * 55 - r, y - r * 0.7, x + k * 55 + r, y + r * 0.7], fill=color)


def _house(d, x, w, h, wall, roof, lit=False):
    top = GROUND_Y - h
    d.rectangle([x, top, x + w, GROUND_Y], fill=wall, outline=OUT, width=6)
    d.polygon([(x - 20, top), (x + w / 2, top - w * 0.45), (x + w + 20, top)], fill=roof, outline=OUT)
    win = (255, 230, 120) if lit else (170, 220, 255)
    for wx in (x + w * 0.15, x + w * 0.6):
        d.rectangle([wx, top + h * 0.18, wx + w * 0.25, top + h * 0.42], fill=win, outline=OUT, width=5)
    d.rectangle([x + w * 0.38, GROUND_Y - h * 0.38, x + w * 0.62, GROUND_Y], fill=(120, 75, 45), outline=OUT, width=5)


def _tree(d, x, scale=1.0, leaf=(70, 170, 80)):
    d.rectangle([x - 18 * scale, GROUND_Y - 160 * scale, x + 18 * scale, GROUND_Y], fill=(120, 80, 50), outline=OUT, width=5)
    for dx, dy, r in ((0, -230, 90), (-60, -180, 70), (60, -180, 70)):
        d.ellipse([x + (dx - r) * scale, GROUND_Y + (dy - r) * scale, x + (dx + r) * scale, GROUND_Y + (dy + r) * scale],
                  fill=leaf, outline=OUT, width=5)


def _floor(d, color, line=None, step=120):
    d.rectangle([0, GROUND_Y, W, H], fill=color)
    d.line([(0, GROUND_Y), (W, GROUND_Y)], fill=OUT, width=6)
    if line:
        for x in range(0, W, step):
            d.line([(x, GROUND_Y), (x - 200, H)], fill=line, width=4)


def _room(d, wall, floor, trim=(255, 255, 255)):
    d.rectangle([0, 0, W, GROUND_Y], fill=wall)
    for y in range(0, GROUND_Y, 90):
        d.line([(0, y), (W, y)], fill=tuple(max(0, c - 10) for c in wall), width=2)
    d.rectangle([0, GROUND_Y - 30, W, GROUND_Y], fill=trim, outline=OUT, width=4)
    _floor(d, floor, tuple(max(0, c - 25) for c in floor))


@lru_cache(maxsize=32)
def background(name: str) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    rng = random.Random(name)

    if name in ("street", "town"):
        _grad(d, (110, 190, 255), (200, 235, 255), 0, GROUND_Y)
        _clouds(d, rng)
        _house(d, 30, 300, 320, (240, 200, 150), (200, 70, 60))
        _house(d, 740, 300, 360, (170, 210, 240), (80, 90, 150))
        _tree(d, 540, 0.9)
        _floor(d, (90, 90, 100))
        d.rectangle([0, GROUND_Y, W, GROUND_Y + 40], fill=(200, 200, 205), outline=OUT, width=4)
        for x in range(40, W, 240):
            d.rectangle([x, GROUND_Y + 250, x + 120, GROUND_Y + 270], fill=(250, 220, 80))
    elif name == "night":
        _grad(d, (15, 20, 55), (60, 50, 110), 0, GROUND_Y)
        for _ in range(70):
            x, y, r = rng.randint(0, W), rng.randint(0, GROUND_Y - 300), rng.choice([2, 3, 4])
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))
        d.ellipse([760, 520, 920, 680], fill=(250, 245, 210))
        d.ellipse([720, 500, 870, 650], fill=(25, 30, 70))
        _house(d, 30, 300, 320, (90, 80, 110), (60, 40, 70), lit=True)
        _house(d, 740, 300, 360, (80, 90, 120), (50, 50, 80), lit=True)
        _floor(d, (40, 40, 60))
    elif name == "school":
        _room(d, (245, 225, 170), (190, 150, 100))
        d.rectangle([140, 560, 800, 960], fill=(40, 90, 60), outline=(150, 100, 60), width=18)
        d.text((540, 730), "", fill=(255, 255, 255))
        for x in range(200, 760, 160):
            d.line([(x, 680), (x + 90, 680)], fill=(230, 230, 230), width=6)
        d.ellipse([850, 560, 990, 700], fill=(255, 255, 255), outline=OUT, width=6)
        d.line([(920, 630), (920, 585)], fill=OUT, width=6)
        d.line([(920, 630), (955, 642)], fill=OUT, width=6)
    elif name == "house":
        _room(d, (200, 220, 240), (170, 120, 80))
        d.rectangle([380, 420, 700, 760], fill=(160, 215, 255), outline=(255, 255, 255), width=18)
        d.line([(540, 420), (540, 760)], fill=(255, 255, 255), width=12)
        d.line([(380, 590), (700, 590)], fill=(255, 255, 255), width=12)
        d.rounded_rectangle([60, 1150, 360, 1360], radius=20, fill=(220, 90, 90), outline=OUT, width=6)
        d.rectangle([860, 1000, 900, 1350], fill=(120, 80, 50), outline=OUT, width=5)
        d.ellipse([820, 900, 940, 1020], fill=(255, 220, 120), outline=OUT, width=5)
    elif name == "park":
        _grad(d, (120, 200, 255), (210, 240, 255), 0, GROUND_Y)
        _clouds(d, rng, 3)
        d.ellipse([820, 480, 980, 640], fill=(255, 225, 80))
        _tree(d, 140, 1.1)
        _tree(d, 930, 1.0)
        d.rectangle([400, 1270, 680, 1290], fill=(130, 85, 55), outline=OUT, width=4)
        _floor(d, (100, 190, 90))
    elif name == "shop":
        _room(d, (250, 240, 220), (220, 220, 225))
        for y in (480, 700, 920):
            d.rectangle([60, y, 1020, y + 22], fill=(150, 100, 60), outline=OUT, width=4)
            for x in range(80, 1000, 70):
                c = rng.choice([(230, 80, 80), (80, 160, 230), (250, 200, 60), (100, 200, 120)])
                d.rectangle([x, y - 80, x + 50, y], fill=c, outline=OUT, width=3)
        d.rectangle([0, 1180, W, 1360], fill=(170, 120, 80), outline=OUT, width=6)
    elif name == "hospital":
        _room(d, (235, 245, 245), (200, 220, 220), (180, 220, 230))
        d.rectangle([700, 1150, 1040, 1250], fill=(255, 255, 255), outline=OUT, width=6)
        d.rectangle([700, 1100, 790, 1160], fill=(200, 230, 255), outline=OUT, width=5)
        d.rectangle([480, 520, 600, 640], fill=(230, 60, 60))
        d.rectangle([520, 540, 560, 620], fill=(255, 255, 255))
        d.rectangle([500, 560, 580, 600], fill=(255, 255, 255))
    elif name == "city":
        _grad(d, (255, 170, 120), (255, 220, 160), 0, GROUND_Y)
        for i, x in enumerate(range(-20, W, 150)):
            h = rng.randint(500, 950)
            c = rng.choice([(70, 80, 110), (90, 100, 130), (60, 70, 95)])
            d.rectangle([x, GROUND_Y - h, x + 135, GROUND_Y], fill=c, outline=OUT, width=5)
            for wy in range(GROUND_Y - h + 30, GROUND_Y - 40, 60):
                for wx in range(x + 18, x + 120, 40):
                    if rng.random() < 0.6:
                        d.rectangle([wx, wy, wx + 22, wy + 32], fill=(255, 230, 140))
        _floor(d, (80, 80, 90))
    elif name == "beach":
        _grad(d, (100, 200, 255), (200, 240, 255), 0, 1080)
        d.ellipse([140, 480, 320, 660], fill=(255, 220, 70))
        d.rectangle([0, 1000, W, GROUND_Y], fill=(40, 150, 220))
        for y in range(1030, GROUND_Y, 60):
            for x in range(0, W, 120):
                d.arc([x, y, x + 80, y + 30], 200, 340, fill=(220, 245, 255), width=5)
        _floor(d, (245, 220, 150))
    elif name == "forest":
        _grad(d, (90, 150, 110), (170, 210, 160), 0, GROUND_Y)
        for x in range(-40, W + 100, 170):
            _tree(d, x + rng.randint(-30, 30), rng.uniform(0.9, 1.4), rng.choice([(50, 130, 60), (40, 110, 55), (70, 150, 70)]))
        _floor(d, (90, 140, 70))
    elif name == "space":
        _grad(d, (5, 5, 20), (30, 15, 60), 0, H)
        for _ in range(140):
            x, y, r = rng.randint(0, W), rng.randint(0, H), rng.choice([1, 2, 3])
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255))
        d.ellipse([650, 480, 1000, 830], fill=(230, 120, 80), outline=OUT, width=6)
        d.ellipse([560, 620, 1090, 700], outline=(240, 200, 150), width=10)
        _floor(d, (130, 130, 145))
        for _ in range(6):
            x = rng.randint(0, W)
            d.ellipse([x - 60, GROUND_Y + 60, x + 60, GROUND_Y + 110], fill=(110, 110, 125))
    elif name == "stage":
        d.rectangle([0, 0, W, GROUND_Y], fill=(30, 20, 40))
        d.polygon([(540, 0), (180, GROUND_Y), (900, GROUND_Y)], fill=(80, 70, 100))
        for x0, x1 in ((0, 220), (860, W)):
            d.rectangle([x0, 0, x1, GROUND_Y], fill=(170, 30, 50))
            for x in range(x0, x1, 40):
                d.line([(x, 0), (x, GROUND_Y)], fill=(130, 20, 40), width=6)
        d.rectangle([0, 0, W, 120], fill=(150, 25, 45))
        _floor(d, (140, 90, 60), (110, 70, 45))
    elif name == "castle":
        _grad(d, (150, 170, 220), (220, 220, 240), 0, GROUND_Y)
        d.rectangle([140, 600, 940, GROUND_Y], fill=(170, 170, 180), outline=OUT, width=6)
        for x in range(140, 940, 80):
            d.rectangle([x, 560, x + 50, 600], fill=(170, 170, 180), outline=OUT, width=5)
        d.rectangle([440, 1000, 640, GROUND_Y], fill=(110, 70, 40), outline=OUT, width=6)
        d.polygon([(470, 470), (540, 380), (610, 470)], fill=(180, 40, 60), outline=OUT)
        d.rectangle([480, 470, 600, 600], fill=(160, 160, 170), outline=OUT, width=6)
        _floor(d, (100, 170, 90))
    elif name == "office":
        _room(d, (220, 225, 235), (110, 120, 140))
        for x in (120, 620):
            d.rectangle([x, 500, x + 340, 760], fill=(150, 200, 240), outline=(255, 255, 255), width=14)
        d.rectangle([60, 1150, 1020, 1200], fill=(140, 100, 70), outline=OUT, width=5)
        d.rectangle([420, 1030, 660, 1150], fill=(40, 40, 50), outline=OUT, width=5)
    else:  # plain colorful fallback
        _grad(d, (120, 120, 220), (220, 160, 220), 0, GROUND_Y)
        _floor(d, (90, 80, 140))
    return img


SETS = ["street", "town", "night", "school", "house", "park", "shop", "hospital", "city", "beach", "forest", "space",
        "stage", "castle", "office"]
