"""
Picks a fresh matchup for each video, keeps them fairly balanced (so the result isn't obvious),
and writes the title, description, tags and voice lines. history.json stops repeats.
"""
import json
import os
import random
from dataclasses import dataclass

from .mobs import NETHER, OVERWORLD

HISTORY = os.path.join(os.path.dirname(__file__), "..", "history.json")
NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
                9: "nine", 10: "ten", 12: "twelve", 15: "fifteen", 20: "twenty"}


@dataclass
class Matchup:
    key: str
    label_a: str
    label_b: str
    team_a: list          # list of Mob
    team_b: list
    color_a: tuple
    color_b: tuple
    arena: str            # block texture for the floor
    title: str
    intro_line: str


def load_history():
    try:
        with open(HISTORY) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"recent": [], "posted": []}


def save_history(h):
    h["recent"] = h["recent"][-60:]
    with open(HISTORY, "w") as f:
        json.dump(h, f, indent=2)


def spoken(n):
    return NUMBER_WORDS.get(n, str(n))


def say(label: str, capital: bool = True) -> str:
    """'10 Zombies' -> 'Ten zombies' (reads better in the voiceover)."""
    num, rest = label.split(" ", 1)
    words = rest.replace("Mobs", "mobs")
    text = f"{spoken(int(num))} {words}"
    return text[0].upper() + text[1:] if capital else text


def power(team):
    return sum(m.power for m in team)


def _overworld_vs_nether(rng, pool):
    ow = [m for m in pool if m.dimension == OVERWORLD]
    ne = [m for m in pool if m.dimension == NETHER]
    n = rng.choice([4, 5, 6, 6, 7, 8])
    a = rng.sample(ow, min(n, len(ow)))
    b = rng.sample(ne, min(n, len(ne)))
    while len(b) < len(a):           # fewer nether mob types: repeat some
        b.append(rng.choice(ne))
    n = len(a)
    return (f"ow-ne-{n}-" + ",".join(sorted(m.key for m in a + b)), f"{n} Overworld Mobs", f"{n} Nether Mobs",
            a, b, (90, 200, 90), (230, 70, 50), rng.choice(["block/grass_block_top.png", "block/netherrack.png"]),
            f"{n} Overworld Mobs vs {n} Nether Mobs - Who Wins?",
            f"{spoken(n).capitalize()} Overworld mobs versus {spoken(n)} Nether mobs. Who wins?")


def _army_vs_army(rng, pool):
    """e.g. '10 Zombies vs 3 Piglin Brutes' - counts picked so both sides have similar power."""
    for _ in range(50):
        x, y = rng.sample(pool, 2)
        nx = rng.choice([1, 2, 3, 4, 5, 6, 8, 10])
        ratio = (x.power * nx) / y.power
        ny = max(1, round(ratio * rng.uniform(0.85, 1.15)))
        if 1 <= ny <= 15 and nx + ny <= 22 and not (nx == 1 and ny == 1):
            break
    a, b = [x] * nx, [y] * ny
    la = f"{nx} {x.plural if nx > 1 else x.name}"
    lb = f"{ny} {y.plural if ny > 1 else y.name}"
    arena = rng.choice(["block/stone_bricks.png", "block/sand.png", "block/oak_planks.png", "block/blackstone.png",
                        "block/deepslate_tiles.png"])
    return (f"army-{x.key}-{nx}-{y.key}-{ny}", la, lb, a, b, (80, 170, 255), (255, 170, 40), arena,
            f"{la} vs {lb} - Who Wins?",
            f"{spoken(nx).capitalize()} {(x.plural if nx > 1 else x.name).lower()} versus "
            f"{spoken(ny)} {(y.plural if ny > 1 else y.name).lower()}. Who wins?")


def _themed(rng, pool):
    teams = {
        "Undead": [m for m in pool if "undead" in m.tags],
        "Illagers": [m for m in pool if "illager" in m.tags],
        "Ranged Mobs": [m for m in pool if m.attack in ("arrow", "fireball")],
        "Melee Mobs": [m for m in pool if m.attack == "melee" and "strong" not in m.tags],
        "Tank Mobs": [m for m in pool if "strong" in m.tags or m.hp >= 40],
        "Fast Mobs": [m for m in pool if m.speed >= 1.9],
    }
    teams = {k: v for k, v in teams.items() if len(v) >= 2}
    na, nb = rng.sample(sorted(teams), 2)
    a = [m for m in teams[na]]
    b = [m for m in teams[nb] if m not in a] or teams[nb]
    # top up the weaker side until power is close
    while power(a) < power(b) * 0.85 and len(a) < 12:
        a.append(rng.choice(teams[na]))
    while power(b) < power(a) * 0.85 and len(b) < 12:
        b.append(rng.choice(teams[nb]))
    return (f"theme-{na}-{nb}-{len(a)}-{len(b)}", f"{len(a)} {na}", f"{len(b)} {nb}", a, b,
            (120, 220, 255), (255, 110, 200), rng.choice(["block/obsidian.png", "block/end_stone.png",
                                                          "block/nether_bricks.png", "block/stone_bricks.png"]),
            f"{len(a)} {na} vs {len(b)} {nb} - Who Wins?",
            f"{spoken(len(a)).capitalize()} {na.lower()} versus {spoken(len(b))} {nb.lower()}. Who wins?")


def pick(pool, seed: int) -> Matchup:
    rng = random.Random(seed)
    history = load_history()
    recent = set(history.get("recent", []))
    makers = [_overworld_vs_nether, _army_vs_army, _army_vs_army, _themed]
    for _ in range(40):
        result = rng.choice(makers)(rng, pool)
        if result[0] not in recent:
            break
    key, la, lb, a, b, ca, cb, arena, title, intro = result
    if rng.random() < 0.5:  # mix up which side is on top
        la, lb, a, b, ca, cb = lb, la, b, a, cb, ca
    title = f"{la} vs {lb} - Who Wins?"
    intro = f"{say(la)} versus {say(lb, False)}. Who wins?"
    return Matchup(key, la, lb, a, b, ca, cb, arena, title, intro)


def remember(matchup: Matchup, video_id: str | None):
    h = load_history()
    h.setdefault("recent", []).append(matchup.key)
    if video_id:
        h.setdefault("posted", []).append({"id": video_id, "title": matchup.title})
        h["posted"] = h["posted"][-300:]
    save_history(h)


def youtube_text(m: Matchup, winner_label: str | None = None):
    title = f"{m.title} #minecraft #shorts"
    if len(title) > 100:
        title = title[:97] + "..."
    description = (
        f"{m.label_a} vs {m.label_b} in a Minecraft mob battle - who do you think wins?\n"
        "Comment the next matchup you want to see!\n\n"
        "#minecraft #shorts #minecraftmobs #mobbattle #minecraftshorts"
    )
    tags = ["minecraft", "minecraft mobs", "mob battle", "minecraft shorts", "who wins", "mob vs mob",
            "minecraft fight", m.label_a, m.label_b]
    return title, description, tags
