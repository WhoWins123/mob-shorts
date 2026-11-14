"""Draws the story frames: background, characters, effects, the hook header and word-by-word captions."""
import math
import random
from dataclasses import dataclass, field

from PIL import Image, ImageDraw

from .chars import CROWD, draw_character
from .scenes import GROUND_Y, H, W, background
from .text import font, wrap

FPS = 30


@dataclass
class Beat:
    say: str
    set: str
    cast: list            # [(role, expr)]
    fx: str
    start: float = 0.0
    end: float = 0.0
    words: list = field(default_factory=list)   # [(word, start, end)] absolute seconds


def cast_positions(n):
    return {1: [540], 2: [300, 780], 3: [190, 540, 890]}.get(n, [540])


class StoryRenderer:
    def __init__(self, story, beats, seed):
        self.story = story
        self.beats = beats
        self.rng = random.Random(seed)
        self.total = beats[-1].end
        self.header = self._header()
        self.particles = []
        self._chunks = [self._caption_chunks(b) for b in beats]

    # ------------------------------------------------------------------ static header

    def _header(self):
        """'IN THIS WORLD,' + the rule, on a dark band at the top. Drawn once, pasted every frame."""
        top = self.story["top"].upper()
        rule = self.story["rule"].replace("*", "").upper()
        hot = {w.strip("*.,!?").upper() for w in self.story["rule"].split() if w.startswith("*")}
        f1, f2 = font(64), font(76)
        lines = wrap(rule, f2, 960)
        while len(lines) > 3 and f2.size > 50:
            f2 = font(f2.size - 6)
            lines = wrap(rule, f2, 960)
        height = 60 + 80 + len(lines) * (f2.size + 10) + 30
        img = Image.new("RGBA", (W, height), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([30, 0, W - 30, height], radius=36, fill=(10, 10, 20, 170))
        d.text((W / 2, 70), top, font=f1, fill=(255, 220, 60), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
        y = 140
        for line in lines:
            x = (W - f2.getlength(line)) / 2
            for word in line.split(" "):
                color = (255, 220, 60) if word.strip(".,!?") in hot else (255, 255, 255)
                d.text((x, y + f2.size / 2), word, font=f2, fill=color, anchor="lm", stroke_width=7,
                       stroke_fill=(0, 0, 0))
                x += f2.getlength(word + " ")
            y += f2.size + 10
        return img

    # ------------------------------------------------------------------ captions

    @staticmethod
    def _caption_chunks(beat):
        chunks, cur = [], []
        for w in beat.words:
            cur.append(w)
            text = " ".join(x[0] for x in cur)
            if len(cur) >= 3 or len(text) >= 14 or w[0][-1:] in ".,!?":
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        return chunks

    def _draw_caption(self, d, bi, t):
        chunks = self._chunks[bi]
        if not chunks:
            return
        current = chunks[0]
        for c in chunks:
            if c[0][1] <= t:
                current = c
        words = [w[0].upper() for w in current]
        f = font(96)
        while sum(f.getlength(w) for w in words) + f.getlength(" ") * 1.8 * (len(words) - 1) > 1000 and f.size > 60:
            f = font(f.size - 6)
        space = f.getlength(" ") * 1.8
        total = sum(f.getlength(w) for w in words) + space * (len(words) - 1)
        x = (W - total) / 2
        y = 1580
        pop = 1.0
        for (word, ws, we), text in zip(current, words):
            active = ws <= t < max(we, ws + 0.12)
            color = (255, 230, 40) if active else (255, 255, 255)
            fw = f
            if active and t - ws < 0.1:
                pop = 1.08
                fw = font(int(f.size * pop))
            d.text((x + f.getlength(text) / 2, y), text, font=fw, fill=color, anchor="mm", stroke_width=11,
                   stroke_fill=(0, 0, 0))
            x += f.getlength(text) + space

    # ------------------------------------------------------------------ effects

    def _spawn(self, fx, t, beat_t):
        rng = self.rng
        if fx == "rain":
            for _ in range(6):
                self.particles.append(["rain", rng.uniform(0, W), rng.uniform(-200, 0), 0, 40, 0.8])
        elif fx == "snow":
            for _ in range(2):
                self.particles.append(["snow", rng.uniform(0, W), -20, rng.uniform(-1, 1), 4, 6])
        elif fx in ("money", "confetti"):
            for _ in range(2):
                self.particles.append([fx, rng.uniform(0, W), -40, rng.uniform(-2, 2), rng.uniform(6, 10), 5,
                                       rng.choice([(240, 80, 80), (80, 200, 240), (250, 220, 60), (120, 230, 120),
                                                   (220, 120, 240)])])
        elif fx == "hearts" and rng.random() < 0.4:
            self.particles.append(["heart", rng.uniform(150, 930), GROUND_Y - 100, rng.uniform(-1, 1), -5, 3])
        elif fx == "sparkle" and rng.random() < 0.5:
            self.particles.append(["star", rng.uniform(150, 930), rng.uniform(700, 1300), 0, 0, 0.7])

    def _draw_particles(self, d, dt):
        keep = []
        for p in self.particles:
            kind = p[0]
            p[1] += p[3]
            p[2] += p[4]
            p[5] -= dt
            if p[5] <= 0 or p[2] > H:
                continue
            keep.append(p)
            x, y = p[1], p[2]
            if kind == "rain":
                d.line([x, y, x - 8, y + 50], fill=(170, 200, 255), width=4)
            elif kind == "snow":
                d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 255, 255))
            elif kind == "money":
                d.rectangle([x - 34, y - 18, x + 34, y + 18], fill=(110, 200, 110), outline=(30, 90, 30), width=4)
                d.text((x, y), "$", font=font(30), fill=(30, 90, 30), anchor="mm")
            elif kind == "confetti":
                d.rectangle([x - 9, y - 5, x + 9, y + 5], fill=p[6])
            elif kind == "heart":
                r = 22
                d.ellipse([x - r, y - r, x, y], fill=(240, 60, 100))
                d.ellipse([x, y - r, x + r, y], fill=(240, 60, 100))
                d.polygon([(x - r, y - r / 2), (x + r, y - r / 2), (x, y + r)], fill=(240, 60, 100))
            elif kind == "star":
                s = 26 * p[5]
                d.polygon([(x, y - s), (x + s * 0.3, y - s * 0.3), (x + s, y), (x + s * 0.3, y + s * 0.3), (x, y + s),
                           (x - s * 0.3, y + s * 0.3), (x - s, y), (x - s * 0.3, y - s * 0.3)], fill=(255, 240, 120))
        self.particles = keep

    # ------------------------------------------------------------------ frame

    def frame(self, t):
        bi = 0
        for i, b in enumerate(self.beats):
            if b.start <= t:
                bi = i
        beat = self.beats[bi]
        bt = t - beat.start
        prev_roles = {r for r, _ in self.beats[bi - 1].cast} if bi > 0 else set()

        img = background(beat.set).copy()
        if beat.fx == "dark":
            img = Image.blend(img, Image.new("RGB", img.size, (10, 10, 30)), 0.45)

        # characters
        cast = beat.cast[:3]
        xs = cast_positions(len(cast))
        for (role, expr), x in zip(cast, xs):
            if role == "crowd":
                for k, r in enumerate(CROWD[:3]):
                    cx = x + (k - 1) * 150
                    draw_character(img, r, cx, GROUND_Y + 50 + (k % 2) * 30, 1.6, expr, t + k)
                continue
            scale = 2.3 if role == "W" else 2.1
            y = GROUND_Y + 60
            bob = math.sin(t * 3.2 + x) * 6
            if role not in prev_roles and bt < 0.35:  # slides in
                k = 1 - bt / 0.35
                x += (-1 if x < W / 2 else 1) * k * k * 700
            if expr in ("shock", "scared") and bt < 0.4:
                y -= math.sin(bt / 0.4 * math.pi) * 60
            if expr == "scared":
                x += math.sin(t * 60) * 4
            draw_character(img, role, x, y + bob, scale, expr, t)
            if expr in ("shock", "scared") and bt < 1.2:
                ImageDraw.Draw(img).text((x + 140, y - 590), "!", font=font(130), fill=(255, 60, 60), anchor="mm",
                                         stroke_width=8, stroke_fill=(0, 0, 0))

        d = ImageDraw.Draw(img, "RGBA")
        self._spawn(beat.fx, t, bt)
        self._draw_particles(d, 1 / FPS)

        if beat.fx == "zoom":
            k = 1 + 0.12 * min(1, bt / max(0.5, beat.end - beat.start))
            cw, ch = int(W / k), int(H / k)
            x0, y0 = (W - cw) // 2, int((H - ch) * 0.62)
            img = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)
            d = ImageDraw.Draw(img, "RGBA")
        if beat.fx == "shake" and bt < 0.6:
            dx, dy = self.rng.randint(-18, 18), self.rng.randint(-18, 18)
            img = img.transform(img.size, Image.AFFINE, (1, 0, dx, 0, 1, dy), fillcolor=(0, 0, 0))
            d = ImageDraw.Draw(img, "RGBA")
        if beat.fx == "flash" and bt < 0.3:
            img = Image.blend(img, Image.new("RGB", img.size, (255, 255, 255)), 0.8 * (1 - bt / 0.3))
            d = ImageDraw.Draw(img, "RGBA")

        img.paste(self.header, (0, 90), self.header)
        self._draw_caption(d, bi, t)
        # thin progress bar
        d.rectangle([0, H - 14, W * min(1, t / self.total), H], fill=(255, 220, 60))
        return img
