"""
The battle. A simple top-down arena measured in blocks: team A starts at the top, team B at the
bottom. Everything runs at the video frame rate and records a snapshot per frame for rendering,
plus timed events for sound effects and the voiceover.
"""
import math
import random
from dataclasses import dataclass, field

from .mobs import Mob

FPS = 30
DT = 1.0 / FPS
ARENA_W = 11.0
ARENA_H = 12.5
MAX_TIME = 45.0
DEATH_FRAMES = 16
DAMAGE_SCALE = 0.5   # slows fights down so they last ~15-30s; keeps the real stat ratios


def top_limit(mob):
    """How close to the top edge a mob may stand so its sprite doesn't cover the title."""
    z = (1.5 if mob.key == "ghast" else 1.0) if mob.flying else 0.0
    return max(0.3, mob.height + z - 1.4)


@dataclass
class Unit:
    id: int
    mob: Mob
    team: int
    x: float
    y: float
    hp: float
    cooldown: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    hurt: int = 0          # frames of red flash left
    fuse: float = -1.0     # creeper fuse timer (-1 = not lit)
    dying: int = -1        # frames since death (-1 = alive)
    bob: float = 0.0

    @property
    def alive(self):
        return self.dying < 0

    @property
    def z(self):
        if not self.mob.flying:
            return 0.0
        base = 1.5 if self.mob.key == "ghast" else 1.0
        return base + 0.15 * math.sin(self.bob)


@dataclass
class Projectile:
    kind: str              # "arrow" | "fireball"
    team: int
    x: float
    y: float
    z: float
    vx: float
    vy: float
    damage: float
    target: int
    big: bool = False      # ghast fireball (explodes)
    life: float = 3.0


@dataclass
class Particle:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    color: tuple
    size: float
    life: float


@dataclass
class Popup:
    x: float
    y: float
    z: float
    text: str
    life: float = 0.8


@dataclass
class Snapshot:
    units: list            # tuples (key, team, x, y, z, hp_frac, hurt, white, dying, facing_left)
    projectiles: list      # tuples (kind, x, y, z, angle, big)
    particles: list        # tuples (x, y, z, color, size)
    popups: list           # tuples (x, y, z, text, alpha)
    alive: tuple           # (alive A, alive B)
    shake: float


@dataclass
class Result:
    frames: list
    events: list           # (time, kind, info)
    winner: int            # 0 or 1, -1 = draw
    survivors: list        # mob keys still alive on the winning team
    first_blood: float = -1.0
    last_stand: tuple = None   # (time, team, mob) when a team got down to its last unit
    team_size: tuple = (0, 0)


class Battle:
    def __init__(self, team_a, team_b, seed: int):
        self.rng = random.Random(seed)
        self.units = []
        self.projectiles = []
        self.particles = []
        self.popups = []
        self.events = []
        self.time = 0.0
        self.shake = 0.0
        self.first_blood = -1.0
        self.last_stand = None
        self._place(team_a, 0)
        self._place(team_b, 1)
        self.team_size = (len(team_a), len(team_b))

    def _place(self, mobs, team):
        n = len(mobs)
        cols = min(n, 6)
        rows = math.ceil(n / cols)
        for i, mob in enumerate(mobs):
            r, c = divmod(i, cols)
            in_row = min(cols, n - r * cols)
            x = ARENA_W / 2 + (c - (in_row - 1) / 2) * min(1.7, (ARENA_W - 1.5) / max(1, in_row - 1) if in_row > 1 else 1.7)
            depth = 1.0 + r * 1.5
            y = max(depth, top_limit(mob)) if team == 0 else ARENA_H - depth
            u = Unit(len(self.units), mob, team, x + self.rng.uniform(-0.2, 0.2), y, mob.hp)
            u.cooldown = self.rng.uniform(0.2, 0.9)
            u.bob = self.rng.uniform(0, 6.28)
            self.units.append(u)

    # ------------------------------------------------------------------ helpers

    def alive_count(self, team):
        return sum(1 for u in self.units if u.team == team and u.alive)

    def nearest_enemy(self, u):
        best, bd = None, 1e9
        for o in self.units:
            if o.team != u.team and o.alive:
                d = (o.x - u.x) ** 2 + (o.y - u.y) ** 2
                if d < bd:
                    best, bd = o, d
        return best, math.sqrt(bd) if best else 1e9

    def event(self, kind, info=None):
        self.events.append((round(self.time, 3), kind, info))

    def damage(self, target, amount, source_x=None, source_y=None, knock=0.0):
        if not target.alive:
            return
        amount = round(amount * DAMAGE_SCALE * self.rng.uniform(0.85, 1.15), 1)
        target.hp -= amount
        target.hurt = 6
        self.popups.append(Popup(target.x, target.y, target.mob.height + target.z + 0.2, f"-{amount:g}"))
        if knock and source_x is not None:
            dx, dy = target.x - source_x, target.y - source_y
            d = math.hypot(dx, dy) or 1
            target.vx += dx / d * knock
            target.vy += dy / d * knock
        if target.hp <= 0:
            target.hp = 0
            target.dying = 0
            self.event("death", target.mob.key)
            if self.first_blood < 0:
                self.first_blood = self.time
            left = self.alive_count(target.team)
            if left == 1 and self.last_stand is None and self.team_size[target.team] > 2:
                last = next(u for u in self.units if u.team == target.team and u.alive)
                self.last_stand = (self.time, target.team, last.mob)

    def explode(self, x, y, radius, power, source=None):
        self.event("explosion")
        self.shake = 1.0
        for _ in range(26):
            a = self.rng.uniform(0, 6.28)
            s = self.rng.uniform(1, 5)
            col = self.rng.choice([(255, 255, 255), (220, 220, 220), (170, 170, 170), (255, 200, 80)])
            self.particles.append(Particle(x, y, 0.5, math.cos(a) * s, math.sin(a) * s, self.rng.uniform(1, 4),
                                           col, self.rng.uniform(0.25, 0.6), self.rng.uniform(0.4, 0.9)))
        for o in self.units:
            if not o.alive or o is source:
                continue
            d = math.hypot(o.x - x, o.y - y)
            if d < radius:
                self.damage(o, power * (1 - d / radius) + 1, x, y, knock=3.0)

    # ------------------------------------------------------------------ step

    def step(self):
        self.time += DT
        self.shake = max(0.0, self.shake - DT * 2.5)

        for u in self.units:
            u.bob += DT * 2.5
            if u.hurt > 0:
                u.hurt -= 1
            if not u.alive:
                u.dying += 1
                if u.dying == DEATH_FRAMES:
                    self.event("poof")
                    for _ in range(12):
                        self.particles.append(Particle(u.x + self.rng.uniform(-0.4, 0.4), u.y, u.z + 0.6,
                                                       self.rng.uniform(-1, 1), self.rng.uniform(-1, 1),
                                                       self.rng.uniform(0.5, 2), (235, 235, 235),
                                                       self.rng.uniform(0.2, 0.35), 0.6))
                continue

            # knockback slides out
            u.x += u.vx * DT
            u.y += u.vy * DT
            u.vx *= 0.82
            u.vy *= 0.82

            target, dist = self.nearest_enemy(u)
            if target is None:
                continue
            m = u.mob

            if m.attack == "explode" and u.fuse >= 0:
                u.fuse += DT
                if u.fuse >= m.cooldown:
                    u.hp = 0
                    u.dying = DEATH_FRAMES  # gone instantly
                    self.explode(u.x, u.y, 3.4, m.damage, source=u)
                    self.event("death", m.key)
                    if self.first_blood < 0:
                        self.first_blood = self.time
                continue

            u.cooldown -= DT
            if dist > m.range:
                dx, dy = target.x - u.x, target.y - u.y
                d = math.hypot(dx, dy) or 1
                u.x += dx / d * m.speed * DT
                u.y += dy / d * m.speed * DT
            elif u.cooldown <= 0:
                u.cooldown = m.cooldown * self.rng.uniform(0.9, 1.15)
                self.attack(u, target)

        self._separate()
        self._projectiles()
        self._particles()

    def attack(self, u, target):
        m = u.mob
        if m.attack == "melee":
            self.event("hit", m.key)
            self.damage(target, m.damage, u.x, u.y, knock=2.2)
        elif m.attack == "explode":
            u.fuse = 0.0
            self.event("fuse")
        else:
            big = m.key == "ghast"
            speed = 15.0 if m.attack == "arrow" else (7.0 if big else 9.0)
            sz = u.z + m.height * 0.6
            dx, dy = target.x - u.x, target.y - u.y
            d = math.hypot(dx, dy) or 1
            self.projectiles.append(Projectile(m.attack, u.team, u.x, u.y, sz, dx / d * speed, dy / d * speed,
                                               m.damage, target.id, big))
            self.event("shoot" if m.attack == "arrow" else "fireball")

    def _separate(self):
        live = [u for u in self.units if u.alive]
        for i, a in enumerate(live):
            for b in live[i + 1:]:
                if a.mob.flying != b.mob.flying:
                    continue
                dx, dy = b.x - a.x, b.y - a.y
                d = math.hypot(dx, dy)
                min_d = 0.75
                if 0 < d < min_d:
                    push = (min_d - d) / 2
                    a.x -= dx / d * push
                    a.y -= dy / d * push
                    b.x += dx / d * push
                    b.y += dy / d * push
        for u in live:
            u.x = min(ARENA_W - 0.4, max(0.4, u.x))
            u.y = min(ARENA_H - 0.3, max(top_limit(u.mob), u.y))

    def _projectiles(self):
        keep = []
        for p in self.projectiles:
            p.x += p.vx * DT
            p.y += p.vy * DT
            p.life -= DT
            if p.kind == "fireball" and self.rng.random() < 0.6:
                self.particles.append(Particle(p.x, p.y, p.z, 0, 0, 0.5, (255, 140, 30), 0.18, 0.3))
            hit = None
            for o in self.units:
                if o.alive and o.team != p.team and math.hypot(o.x - p.x, o.y - p.y) < 0.55:
                    hit = o
                    break
            if hit:
                if p.big:
                    self.explode(p.x, p.y, 2.2, p.damage)
                else:
                    self.damage(hit, p.damage, p.x - p.vx, p.y - p.vy, knock=1.2)
                    self.event("arrow_hit" if p.kind == "arrow" else "burn")
                continue
            if p.life > 0 and 0 <= p.x <= ARENA_W and 0 <= p.y <= ARENA_H:
                keep.append(p)
        self.projectiles = keep

    def _particles(self):
        keep = []
        for p in self.particles:
            p.x += p.vx * DT
            p.y += p.vy * DT
            p.z = max(0.0, p.z + p.vz * DT)
            p.vz -= 6 * DT
            p.life -= DT
            if p.life > 0:
                keep.append(p)
        self.particles = keep
        pops = []
        for p in self.popups:
            p.z += DT * 1.2
            p.life -= DT
            if p.life > 0:
                pops.append(p)
        self.popups = pops

    # ------------------------------------------------------------------ snapshot / run

    def snapshot(self) -> Snapshot:
        units = []
        for u in self.units:
            if u.dying >= DEATH_FRAMES:
                continue
            white = u.fuse >= 0 and int(u.fuse * 8) % 2 == 0
            target, _ = self.nearest_enemy(u) if u.alive else (None, 0)
            facing_left = target is not None and target.x < u.x
            units.append((u.mob.key, u.team, u.x, u.y, u.z, u.hp / u.mob.hp, u.hurt > 0 or u.dying >= 0,
                          white, u.dying, facing_left))
        projectiles = [(p.kind, p.x, p.y, p.z, math.atan2(p.vy, p.vx), p.big) for p in self.projectiles]
        particles = [(p.x, p.y, p.z, p.color, p.size) for p in self.particles]
        popups = [(p.x, p.y, p.z, p.text, min(1.0, p.life / 0.3)) for p in self.popups]
        return Snapshot(units, projectiles, particles, popups, (self.alive_count(0), self.alive_count(1)), self.shake)

    def run(self) -> Result:
        frames = [self.snapshot()]
        while self.time < MAX_TIME:
            self.step()
            frames.append(self.snapshot())
            a, b = self.alive_count(0), self.alive_count(1)
            dying = any(0 <= u.dying < DEATH_FRAMES for u in self.units)
            if (a == 0 or b == 0) and not dying and not self.projectiles:
                break
        a, b = self.alive_count(0), self.alive_count(1)
        if a and not b:
            winner = 0
        elif b and not a:
            winner = 1
        elif a == b == 0:
            winner = -1
        else:  # time ran out: more health left wins
            hp = [sum(u.hp for u in self.units if u.team == t and u.alive) for t in (0, 1)]
            winner = 0 if hp[0] > hp[1] else 1
        survivors = [u.mob.key for u in self.units if u.alive and u.team == winner]
        return Result(frames, self.events, winner, survivors, self.first_blood, self.last_stand, self.team_size)
