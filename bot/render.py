"""Draws every frame (1080x1920) and pipes them into ffmpeg."""
import math
import os
import random
import subprocess

from PIL import Image, ImageDraw, ImageFont

from .mobs import BY_KEY
from .sim import ARENA_H, ARENA_W, DEATH_FRAMES, FPS
from .sprites import PX_PER_BLOCK as PX

W, H = 1080, 1920
AX = (W - ARENA_W * PX) / 2          # arena left edge on screen
AY = 560                             # arena top edge on screen
FONT = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "Poppins-Bold.ttf")
GRASS_TINT = (124, 189, 107)


def font(size):
    return ImageFont.truetype(FONT, size)


def to_screen(x, y, z=0.0):
    return AX + x * PX, AY + y * PX - z * PX


class Renderer:
    def __init__(self, sprites, textures, matchup):
        self.sprites = sprites
        self.m = matchup
        self.background = self._background(textures)
        self.f_title = self._fit_font([matchup.label_a, matchup.label_b], 980, 92)
        self.f_big = font(150)
        self.f_mid = font(64)
        self.f_small = font(40)
        self.f_pop = font(38)
        self._rot_cache = {}

    # ------------------------------------------------------------------ static parts

    def _fit_font(self, texts, width, start):
        size = start
        while size > 40:
            f = font(size)
            if all(f.getlength(t.upper()) <= width for t in texts):
                return f
            size -= 4
        return font(size)

    def _background(self, textures):
        img = Image.new("RGB", (W, H), (18, 16, 28))
        d = ImageDraw.Draw(img)
        for yy in range(H):  # vertical gradient
            t = yy / H
            d.line([(0, yy), (W, yy)], fill=(int(20 + 18 * t), int(16 + 8 * t), int(34 + 10 * t)))

        tex = textures.get(self.m.arena) or textures.get("block/stone_bricks.png")
        if tex is not None:
            if "grass_block_top" in self.m.arena:  # grass is grey in the file; the game tints it green
                gray = tex.convert("L")
                tex = Image.merge("RGB", [gray.point(lambda v, c=c: v * c // 255) for c in GRASS_TINT])
            tex = tex.convert("RGB")
            tile = tex.resize((PX, PX), Image.NEAREST)
            floor = Image.new("RGB", (int(ARENA_W * PX), int(ARENA_H * PX)))
            for ty in range(0, floor.height, PX):
                for tx in range(0, floor.width, PX):
                    floor.paste(tile, (tx, ty))
        else:
            floor = Image.new("RGB", (int(ARENA_W * PX), int(ARENA_H * PX)), (70, 70, 80))
        # darken the floor edges a little so the mobs pop
        shade = Image.new("L", floor.size, 0)
        sd = ImageDraw.Draw(shade)
        for i in range(30):
            sd.rectangle([i * 3, i * 3, floor.width - i * 3, floor.height - i * 3], outline=110 - i * 3)
        floor = Image.composite(Image.new("RGB", floor.size, (0, 0, 0)), floor, shade)
        img.paste(floor, (int(AX), AY))
        d.rectangle([AX - 6, AY - 6, AX + floor.width + 5, AY + floor.height + 5], outline=(0, 0, 0), width=6)
        d.rectangle([AX - 10, AY - 10, AX + floor.width + 9, AY + floor.height + 9], outline=(255, 255, 255), width=3)
        return img

    # ------------------------------------------------------------------ text helpers

    def text(self, d, xy, s, f, fill, anchor="mm", stroke=8):
        d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))

    def header(self, img, d, alive, show_who=True):
        m = self.m
        self.text(d, (W / 2, 80), m.label_a.upper(), self.f_title, m.color_a)
        self.text(d, (W / 2, 168), "VS", font(70), (255, 255, 255))
        self.text(d, (W / 2, 252), m.label_b.upper(), self.f_title, m.color_b)
        if show_who:
            self.text(d, (W / 2, 336), "WHO WINS?", font(60), (255, 225, 60))
        # alive counters with a head icon of each team's first mob
        for team, (x, color) in enumerate([(150, m.color_a), (W - 150, m.color_b)]):
            mob = (m.team_a if team == 0 else m.team_b)[0]
            icon = self.sprites.icons.get(mob.key)
            if icon:
                img.paste(icon, (int(x - icon.width - 12), 300), icon)
            self.text(d, (x + 8, 336), str(alive[team]), font(58), color, anchor="lm")

    # ------------------------------------------------------------------ the arena

    def draw_arena(self, img, snap, show_bars=True):
        d = ImageDraw.Draw(img)
        sx = sy = 0
        if snap.shake > 0:
            sx = random.uniform(-1, 1) * 14 * snap.shake
            sy = random.uniform(-1, 1) * 14 * snap.shake

        units = sorted(snap.units, key=lambda u: u[3])
        # shadows + team rings first
        for key, team, x, y, z, hp, hurt, white, dying, _ in units:
            px, py = to_screen(x, y)
            px += sx
            py += sy
            r = 26 if BY_KEY[key].height < 2.5 else 38
            d.ellipse([px - r, py - r * 0.4, px + r, py + r * 0.4], fill=(0, 0, 0))
            col = self.m.color_a if team == 0 else self.m.color_b
            d.ellipse([px - r - 4, py - r * 0.4 - 3, px + r + 4, py + r * 0.4 + 3], outline=col, width=5)

        for key, team, x, y, z, hp, hurt, white, dying, _ in units:
            base = (self.sprites.white if white else self.sprites.flash if hurt else self.sprites.base)[key]
            sprite = base
            if dying >= 0:  # tip over like in the game
                angle = min(90, dying * 90 / (DEATH_FRAMES * 0.6))
                k = (key, int(angle))
                sprite = self._rot_cache.get(k)
                if sprite is None:
                    sprite = self.sprites.flash[key].rotate(angle, expand=True, resample=Image.NEAREST)
                    self._rot_cache[k] = sprite
            px, py = to_screen(x, y, z)
            px += sx
            py += sy
            img.paste(sprite, (int(px - sprite.width / 2), int(py - sprite.height)), sprite)
            if show_bars and dying < 0:
                bw = 76
                top = py - sprite.height - 20
                col = self.m.color_a if team == 0 else self.m.color_b
                d.rectangle([px - bw / 2 - 3, top - 3, px + bw / 2 + 3, top + 13], fill=(0, 0, 0))
                d.rectangle([px - bw / 2, top, px - bw / 2 + bw * max(0, hp), top + 10], fill=col)

        for kind, x, y, z, angle, big in snap.projectiles:
            px, py = to_screen(x, y, z)
            px += sx
            py += sy
            if kind == "arrow":
                dx, dy = math.cos(angle) * 22, math.sin(angle) * 22
                d.line([px - dx, py - dy, px + dx, py + dy], fill=(110, 75, 40), width=6)
                d.line([px + dx * 0.6, py + dy * 0.6, px + dx, py + dy], fill=(200, 200, 200), width=8)
            else:
                r = 20 if big else 11
                d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 120, 20))
                d.ellipse([px - r * 0.5, py - r * 0.5, px + r * 0.5, py + r * 0.5], fill=(255, 235, 120))

        for x, y, z, color, size in snap.particles:
            px, py = to_screen(x, y, z)
            s = size * PX / 2
            d.rectangle([px - s + sx, py - s + sy, px + s + sx, py + s + sy], fill=color)

        for x, y, z, text, alpha in snap.popups:
            px, py = to_screen(x, y, z)
            if alpha > 0.15:
                self.text(d, (px + sx, py + sy), text, self.f_pop, (255, 70, 70), stroke=5)
        return d

    # ------------------------------------------------------------------ frames

    def frame_intro(self, snap, t, intro_len):
        img = self.background.copy()
        d = self.draw_arena(img, snap, show_bars=False)
        self.header(img, d, snap.alive)
        if t > intro_len - 0.8:  # "FIGHT!" pops in
            k = min(1.0, (t - (intro_len - 0.8)) / 0.15)
            self.text(d, (W / 2, AY + ARENA_H * PX / 2), "FIGHT!", font(int(60 + 110 * k)), (255, 225, 60), stroke=12)
        else:
            self.text(d, (W / 2, H - 90), "Comment your guess before the fight!", self.f_small, (255, 255, 255), stroke=6)
        return img

    def frame_fight(self, snap):
        img = self.background.copy()
        d = self.draw_arena(img, snap)
        self.header(img, d, snap.alive)
        self.text(d, (W / 2, H - 90), "Who's winning? Comment!", self.f_small, (255, 255, 255), stroke=6)
        return img

    def frame_end(self, snap, t, winner, survivors):
        img = self.background.copy()
        d = self.draw_arena(img, snap, show_bars=False)
        self.header(img, d, snap.alive, show_who=False)
        k = min(1.0, t / 0.25)
        mid = AY + ARENA_H * PX / 2
        overlay = Image.new("RGBA", (W, 360), (0, 0, 0, int(190 * k)))
        img.paste(overlay, (0, int(mid - 180)), overlay)
        d = ImageDraw.Draw(img)
        if winner < 0:
            line1, color = "IT'S A DRAW!", (255, 255, 255)
            line2 = "Nobody survived"
        else:
            label = self.m.label_a if winner == 0 else self.m.label_b
            color = self.m.color_a if winner == 0 else self.m.color_b
            line1 = f"{label.split(' ', 1)[1].upper()} WIN!"
            line2 = f"{len(survivors)} left standing"
        f1 = self._fit_font([line1], 1000, 120)
        self.text(d, (W / 2, mid - 50), line1, f1, color, stroke=10)
        self.text(d, (W / 2, mid + 70), line2, self.f_mid, (255, 255, 255), stroke=7)
        self.text(d, (W / 2, H - 125), "Who should fight next?", font(54), (255, 225, 60), stroke=7)
        self.text(d, (W / 2, H - 62), "Comment below!", self.f_small, (255, 255, 255), stroke=6)
        return img


def encode(frames_iter, out_path, fps=FPS):
    """frames_iter yields PIL RGB images; writes an H.264 mp4 with no audio."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    count = 0
    for img in frames_iter:
        proc.stdin.write(img.tobytes())
        count += 1
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed while encoding video")
    return count
