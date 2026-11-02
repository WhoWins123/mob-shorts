"""
Mob roster: names, which texture to load, how to build a front-view sprite from it, and
battle stats based on Java Edition (Normal difficulty), lightly tuned so fights read well.

Sprites are cut straight out of Minecraft's own texture files (downloaded from Mojang by
assets.py). Each "part" is (left, top, right, bottom) in the texture -> (x, y) on a small
canvas, measured in texture pixels. Mirrored parts are flipped left-right.
"""
from dataclasses import dataclass, field

OVERWORLD = "overworld"
NETHER = "nether"


@dataclass(frozen=True)
class Part:
    src: tuple            # (l, t, r, b) in texture pixels
    dst: tuple            # (x, y) on the sprite canvas
    mirror: bool = False


@dataclass(frozen=True)
class Mob:
    key: str
    name: str             # singular display name
    plural: str
    dimension: str
    texture: str          # path inside assets/minecraft/textures/
    tex_size: tuple       # expected (w, h) of the texture
    canvas: tuple         # sprite canvas (w, h) in texture pixels
    parts: tuple
    height: float         # in blocks (sprite is scaled to this)
    hp: float
    damage: float
    attack: str           # "melee" | "arrow" | "fireball" | "explode"
    cooldown: float       # seconds between attacks
    range: float          # attack range in blocks
    speed: float          # blocks per second
    flying: bool = False
    head: tuple = (8, 8, 16, 16)  # crop used for the little HUD icon
    tags: tuple = field(default_factory=tuple)

    @property
    def power(self) -> float:
        """Rough strength used to balance matchups."""
        dps = self.damage / self.cooldown
        if self.attack == "explode":
            dps = self.damage / 4.0
        elif self.attack in ("arrow", "fireball"):
            dps *= 1.7  # shooting from range is worth a lot
        return (self.hp * dps) ** 0.5


# ------------------------------------------------------------------ sprite layouts

def humanoid64():  # zombie / husk / drowned (64x64 player-style)
    return (
        Part((44, 20, 48, 32), (0, 8)),              # right arm
        Part((36, 52, 40, 64), (12, 8)),             # left arm
        Part((4, 20, 8, 32), (4, 20)),               # right leg
        Part((20, 52, 24, 64), (8, 20)),             # left leg
        Part((20, 20, 28, 32), (4, 8)),              # body
        Part((8, 8, 16, 16), (4, 0)),                # head
    )


def skeleton32():  # skeleton / stray / wither skeleton (64x32, thin limbs)
    return (
        Part((42, 18, 44, 30), (2, 8)),
        Part((42, 18, 44, 30), (12, 8), True),
        Part((2, 18, 4, 30), (5, 20)),
        Part((2, 18, 4, 30), (9, 20), True),
        Part((20, 20, 28, 32), (4, 8)),
        Part((8, 8, 16, 16), (4, 0)),
    )


def piglin64():  # piglin / zombified piglin / brute (wide 10px head)
    return (
        Part((44, 20, 48, 32), (1, 8)),
        Part((36, 52, 40, 64), (13, 8)),
        Part((4, 20, 8, 32), (5, 20)),
        Part((20, 52, 24, 64), (9, 20)),
        Part((20, 20, 28, 32), (5, 8)),
        Part((8, 8, 18, 16), (4, 0)),
    )


def illager64():  # vindicator / pillager
    return (
        Part((44, 50, 48, 62), (0, 10)),
        Part((44, 50, 48, 62), (12, 10), True),
        Part((4, 26, 8, 38), (4, 22)),
        Part((4, 26, 8, 38), (8, 22), True),
        Part((22, 26, 30, 38), (4, 10)),
        Part((8, 8, 16, 18), (4, 0)),
    )


CREEPER = (
    Part((4, 20, 8, 26), (0, 20)),
    Part((4, 20, 8, 26), (4, 20), True),
    Part((20, 20, 28, 32), (0, 8)),
    Part((8, 8, 16, 16), (0, 0)),
)

SPIDER = tuple(
    [Part((12, 24, 22, 32), (15, 0))]                                # abdomen peeking out behind
    + [Part((20, 2, 36, 4), (0, 6 + 2 * i)) for i in range(4)]       # left legs
    + [Part((20, 2, 36, 4), (24, 6 + 2 * i), True) for i in range(4)]  # right legs
    + [Part((40, 12, 48, 20), (16, 4))]                              # head
)

ENDERMAN = (
    Part((58, 2, 60, 32), (0, 8)),
    Part((58, 2, 60, 32), (10, 8), True),
    Part((58, 2, 60, 32), (3, 20)),
    Part((58, 2, 60, 32), (7, 20), True),
    Part((36, 20, 44, 32), (2, 8)),
    Part((8, 8, 16, 16), (2, 0)),
)

IRON_GOLEM = (
    Part((42, 5, 48, 21), (7, 27)),
    Part((42, 5, 48, 21), (13, 27), True),
    Part((6, 76, 15, 81), (8, 22)),          # waist
    Part((66, 27, 70, 57), (0, 10)),
    Part((66, 27, 70, 57), (22, 10), True),
    Part((11, 51, 29, 63), (4, 10)),         # chest
    Part((8, 8, 16, 18), (9, 0)),            # head
)

BLAZE = (
    Part((2, 18, 4, 26), (1, 4)),
    Part((2, 18, 4, 26), (17, 4)),
    Part((2, 18, 4, 26), (4, 12)),
    Part((2, 18, 4, 26), (14, 12)),
    Part((2, 18, 4, 26), (9, 16)),
    Part((2, 18, 4, 26), (6, 2)),
    Part((2, 18, 4, 26), (12, 2)),
    Part((8, 8, 16, 16), (6, 0)),
)

GHAST = (
    Part((2, 2, 4, 12), (2, 15)),
    Part((2, 2, 4, 11), (7, 15)),
    Part((2, 2, 4, 13), (12, 15)),
    Part((2, 2, 4, 10), (4, 15)),
    Part((2, 2, 4, 12), (10, 15)),
    Part((16, 16, 32, 32), (0, 0)),
)


ROSTER = [
    # ---------------- Overworld
    Mob("zombie", "Zombie", "Zombies", OVERWORLD, "entity/zombie/zombie.png", (64, 64), (16, 32), humanoid64(),
        1.95, hp=20, damage=3, attack="melee", cooldown=1.0, range=1.3, speed=1.6, tags=("undead",)),
    Mob("husk", "Husk", "Husks", OVERWORLD, "entity/zombie/husk.png", (64, 64), (16, 32), humanoid64(),
        1.95, hp=20, damage=3.5, attack="melee", cooldown=1.0, range=1.3, speed=1.6, tags=("undead",)),
    Mob("drowned", "Drowned", "Drowned", OVERWORLD, "entity/zombie/drowned.png", (64, 64), (16, 32), humanoid64(),
        1.95, hp=20, damage=3, attack="melee", cooldown=1.0, range=1.3, speed=1.5, tags=("undead",)),
    Mob("skeleton", "Skeleton", "Skeletons", OVERWORLD, "entity/skeleton/skeleton.png", (64, 32), (16, 32), skeleton32(),
        1.99, hp=20, damage=3, attack="arrow", cooldown=1.6, range=9, speed=1.5, tags=("undead",)),
    Mob("stray", "Stray", "Strays", OVERWORLD, "entity/skeleton/stray.png", (64, 32), (16, 32), skeleton32(),
        1.99, hp=20, damage=3.5, attack="arrow", cooldown=1.6, range=9, speed=1.5, tags=("undead",)),
    Mob("creeper", "Creeper", "Creepers", OVERWORLD, "entity/creeper/creeper.png", (64, 32), (8, 26), CREEPER,
        1.7, hp=20, damage=22, attack="explode", cooldown=1.5, range=1.8, speed=1.4),
    Mob("spider", "Spider", "Spiders", OVERWORLD, "entity/spider/spider.png", (64, 32), (40, 16), SPIDER,
        0.9, hp=16, damage=2, attack="melee", cooldown=0.7, range=1.4, speed=2.4, head=(40, 12, 48, 20),
        tags=("arthropod",)),
    Mob("enderman", "Enderman", "Endermen", OVERWORLD, "entity/enderman/enderman.png", (64, 32), (12, 50), ENDERMAN,
        2.9, hp=40, damage=7, attack="melee", cooldown=1.2, range=1.8, speed=2.6),
    Mob("iron_golem", "Iron Golem", "Iron Golems", OVERWORLD, "entity/iron_golem/iron_golem.png", (128, 128), (26, 43),
        IRON_GOLEM, 2.7, hp=100, damage=11, attack="melee", cooldown=1.5, range=1.9, speed=1.3,
        head=(8, 8, 16, 18), tags=("strong",)),
    Mob("vindicator", "Vindicator", "Vindicators", OVERWORLD, "entity/illager/vindicator.png", (64, 64), (16, 34),
        illager64(), 1.95, hp=24, damage=13, attack="melee", cooldown=1.4, range=1.4, speed=1.9,
        head=(8, 8, 16, 18), tags=("illager",)),
    Mob("pillager", "Pillager", "Pillagers", OVERWORLD, "entity/illager/pillager.png", (64, 64), (16, 34), illager64(),
        1.95, hp=24, damage=4, attack="arrow", cooldown=1.8, range=8, speed=1.7, head=(8, 8, 16, 18),
        tags=("illager",)),
    # ---------------- Nether
    Mob("piglin", "Piglin", "Piglins", NETHER, "entity/piglin/piglin.png", (64, 64), (18, 32), piglin64(),
        1.95, hp=16, damage=8, attack="melee", cooldown=1.1, range=1.4, speed=1.8, head=(8, 8, 18, 16)),
    Mob("zombified_piglin", "Zombified Piglin", "Zombified Piglins", NETHER, "entity/piglin/zombified_piglin.png",
        (64, 64), (18, 32), piglin64(), 1.95, hp=20, damage=8, attack="melee", cooldown=1.2, range=1.4, speed=1.7,
        head=(8, 8, 18, 16), tags=("undead",)),
    Mob("piglin_brute", "Piglin Brute", "Piglin Brutes", NETHER, "entity/piglin/piglin_brute.png", (64, 64), (18, 32),
        piglin64(), 1.95, hp=50, damage=13, attack="melee", cooldown=1.3, range=1.5, speed=1.9,
        head=(8, 8, 18, 16), tags=("strong",)),
    Mob("wither_skeleton", "Wither Skeleton", "Wither Skeletons", NETHER, "entity/skeleton/wither_skeleton.png",
        (64, 32), (16, 32), skeleton32(), 2.4, hp=20, damage=8, attack="melee", cooldown=1.1, range=1.6, speed=1.8,
        tags=("undead",)),
    Mob("blaze", "Blaze", "Blazes", NETHER, "entity/blaze.png", (64, 32), (20, 26), BLAZE,
        1.8, hp=20, damage=5, attack="fireball", cooldown=2.0, range=8, speed=1.5, flying=True),
    Mob("ghast", "Ghast", "Ghasts", NETHER, "entity/ghast/ghast.png", (64, 32), (16, 28), GHAST,
        3.2, hp=10, damage=6, attack="fireball", cooldown=3.0, range=11, speed=1.0, flying=True,
        head=(16, 16, 32, 32)),
]

BY_KEY = {m.key: m for m in ROSTER}
