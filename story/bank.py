"""
Loads the story bank (bot/story/stories/*.txt).

Format - one story per block, blocks separated by a line with ---

    id: loud-dream
    top: In this town,
    rule: the *loudest* dream comes true
    mood: mystery            (mystery | happy | sad - picks the music)
    street | W:sad, crowd:happy | zoom | Every night, the whole town shouts their dreams at the sky.
    ...

Each scene line is:  place | who:face, who:face | effect | what the narrator says
  places:  street town night school house park shop hospital city beach forest space stage castle office
  who:     W mom dad kid girl boy friend teacher bully rival old doctor boss cop king alien ghost robot crowd
  faces:   neutral happy sad angry shock scared cry smirk love
  effects: (empty) zoom shake flash dark rain snow money confetti hearts sparkle
A short "In this town, ..." opening and a comment prompt at the end are added automatically.
"""
import glob
import os
import re

from .chars import LOOKS
from .scenes import SETS

FACES = {"neutral", "happy", "sad", "angry", "shock", "scared", "cry", "smirk", "love"}
EFFECTS = {"", "zoom", "shake", "flash", "dark", "rain", "snow", "money", "confetti", "hearts", "sparkle"}
ROLES = set(LOOKS) | {"crowd"}


def load(folder=None):
    folder = folder or os.path.join(os.path.dirname(__file__), "stories")
    stories, errors = [], []
    for path in sorted(glob.glob(os.path.join(folder, "*.txt"))):
        with open(path, encoding="utf-8") as f:
            blocks = re.split(r"^---\s*$", f.read(), flags=re.M)
        for block in blocks:
            lines = [l.strip() for l in block.strip().splitlines() if l.strip() and not l.strip().startswith("#")]
            if not lines:
                continue
            try:
                stories.append(parse(lines))
            except ValueError as e:
                errors.append(f"{os.path.basename(path)}: {e}")
    return stories, errors


def parse(lines):
    story = {"beats": [], "mood": "mystery"}
    for line in lines:
        if "|" not in line and ":" in line:
            k, v = line.split(":", 1)
            story[k.strip().lower()] = v.strip()
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 4:
            raise ValueError(f"bad scene line: {line}")
        place, who, fx, say = parts
        if place not in SETS:
            raise ValueError(f"unknown place '{place}' in {story.get('id')}")
        if fx not in EFFECTS:
            raise ValueError(f"unknown effect '{fx}' in {story.get('id')}")
        cast = []
        for c in [c.strip() for c in who.split(",") if c.strip()]:
            role, _, face = c.partition(":")
            face = face or "neutral"
            if role not in ROLES or face not in FACES:
                raise ValueError(f"unknown character/face '{c}' in {story.get('id')}")
            cast.append((role, face))
        if not cast:
            raise ValueError(f"scene with nobody in it in {story.get('id')}")
        story["beats"].append({"set": place, "cast": cast[:3], "fx": fx, "say": say})
    for key in ("id", "top", "rule"):
        if key not in story:
            raise ValueError(f"story missing '{key}': {lines[0]}")
    if len(story["beats"]) < 3:
        raise ValueError(f"story {story['id']} needs at least 3 scenes")
    return story


def plain_rule(story):
    return story["rule"].replace("*", "")


def title(story):
    """'In this town,' + 'the *loudest* dream comes true' -> 'In This Town, the LOUDEST Dream Comes True'"""
    small = {"a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "for", "but"}
    words = []
    for i, w in enumerate(story["rule"].split()):
        if w.startswith("*") and w.rstrip(".,!?").endswith("*"):
            words.append(w.replace("*", "").upper())
        elif w.lower() in small:
            words.append(w.lower())
        else:
            words.append(w[:1].upper() + w[1:])
    top = " ".join(x[:1].upper() + x[1:] for x in story["top"].split())
    return f"{top} {' '.join(words)}"
