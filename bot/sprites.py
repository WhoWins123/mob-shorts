"""Builds front-view mob sprites from the official textures (see mobs.py for the layouts)."""
from PIL import Image, ImageOps

from .mobs import Mob

PX_PER_BLOCK = 92  # screen pixels per block in the arena


class Sprites:
    def __init__(self, textures):
        self.textures = textures
        self.base = {}     # mob key -> full-size RGBA sprite
        self.flash = {}    # mob key -> red "hurt" version
        self.white = {}    # mob key -> white version (creeper about to blow)
        self.icons = {}    # mob key -> small head icon
        self.missing = []

    def prepare(self, mobs):
        for mob in mobs:
            img = self.textures.get(mob.texture)
            if img is None or img.size != mob.tex_size:
                self.missing.append(mob.key)
                continue
            sprite = build_sprite(img, mob)
            self.base[mob.key] = sprite
            self.flash[mob.key] = tint(sprite, (255, 40, 40), 0.55)
            self.white[mob.key] = tint(sprite, (255, 255, 255), 0.7)
            head = img.crop(mob.head)
            self.icons[mob.key] = head.resize((head.width * 72 // head.height, 72), Image.NEAREST)
        return [m for m in mobs if m.key in self.base]


def build_sprite(tex: Image.Image, mob: Mob) -> Image.Image:
    canvas = Image.new("RGBA", mob.canvas, (0, 0, 0, 0))
    for part in mob.parts:
        piece = tex.crop(part.src)
        if part.mirror:
            piece = ImageOps.mirror(piece)
        canvas.alpha_composite(piece, part.dst)
    # trim empty rows/columns, then scale with hard pixel edges to the mob's real height
    bbox = canvas.getbbox() or (0, 0, canvas.width, canvas.height)
    canvas = canvas.crop(bbox)
    height = max(24, int(mob.height * PX_PER_BLOCK))
    width = max(8, round(canvas.width * height / canvas.height))
    return canvas.resize((width, height), Image.NEAREST)


def tint(img: Image.Image, color, amount: float) -> Image.Image:
    solid = Image.new("RGBA", img.size, color + (255,))
    mixed = Image.blend(img, solid, amount)
    mixed.putalpha(img.getchannel("A"))
    return mixed
