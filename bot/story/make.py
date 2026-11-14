"""
Makes one "In this world..." story Short and (optionally) posts it.

    python -m bot.story.make            # make a video into out/
    python -m bot.story.make --post     # make it and upload it
    python -m bot.story.make --id loud-dream   # a specific story
"""
import argparse
import json
import os
import random
import subprocess
import time

import numpy as np

from .. import upload
from ..render import encode
from . import bank, sound
from .render import FPS, Beat, StoryRenderer

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "out")
HISTORY = os.path.join(ROOT, "history.json")

ENDINGS = [
    "Would you survive in this world? Comment below!",
    "What would you do in this world? Tell me in the comments!",
    "Would you want to live here? Comment yes or no!",
    "Follow for more weird worlds like this one!",
]


def load_history():
    try:
        with open(HISTORY) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_history(h):
    with open(HISTORY, "w") as f:
        json.dump(h, f, indent=2)


def pick_story(stories, seed, wanted=None):
    if wanted:
        for s in stories:
            if s["id"] == wanted:
                return s
        raise SystemExit(f"no story with id {wanted}")
    h = load_history()
    done = set(h.get("stories_done", []))
    left = [s for s in stories if s["id"] not in done]
    if not left:  # used every story: start the bank over
        print("every story has been posted - starting the bank over")
        h["stories_done"] = []
        save_history(h)
        left = stories
    return random.Random(seed).choice(left)


def build_beats(story, seed):
    rng = random.Random(seed)
    first, last = story["beats"][0], story["beats"][-1]
    hook = {"set": first["set"], "cast": first["cast"], "fx": "zoom",
            "say": f"{story['top']} {bank.plain_rule(story)}."}
    ending = {"set": last["set"], "cast": [("W", "smirk")], "fx": "", "say": rng.choice(ENDINGS)}
    return [hook] + story["beats"] + [ending]


def make_video(story, seed):
    os.makedirs(OUT, exist_ok=True)
    voice = sound.NARRATORS[seed % len(sound.NARRATORS)]
    raw = build_beats(story, seed)

    beats, clips, events = [], [], []
    t = 0.2
    prev_set, prev_roles = None, set()
    for i, b in enumerate(raw):
        samples, words = sound.narrate(b["say"], voice, OUT, f"beat{i}")
        dur = len(samples) / sound.SR
        gap = 0.3 if i < len(raw) - 1 else 1.2
        beat = Beat(b["say"], b["set"], b["cast"], b["fx"], t, t + dur + gap,
                    [(w, t + s, t + e) for w, s, e in words])
        beats.append(beat)
        clips.append((t, samples))
        if b["set"] != prev_set:
            events.append((max(0, t - 0.15), "whoosh"))
        if {r for r, _ in b["cast"]} - prev_roles:
            events.append((t, "pop"))
        if b["fx"] in ("sparkle", "money", "confetti", "hearts"):
            events.append((t + 0.1, "ding"))
        if b["fx"] in ("shake", "flash"):
            events.append((t, "boom"))
        prev_set, prev_roles = b["set"], {r for r, _ in b["cast"]}
        t = beat.end
    total = t
    print(f"story '{story['id']}': {len(beats)} scenes, {total:.1f}s, voice {voice}")

    r = StoryRenderer(story, beats, seed)
    silent = os.path.join(OUT, "video_silent.mp4")
    started = time.time()
    n = encode((r.frame(i / FPS) for i in range(int(total * FPS))), silent)
    print(f"rendered {n} frames in {time.time() - started:.0f}s")

    wav = os.path.join(OUT, "audio.wav")
    sound.mix(total, clips, events, seed, wav, story.get("mood", "mystery"))
    final = os.path.join(OUT, "short.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", final], check=True)
    print("video:", final)
    return final, total


def youtube_text(story):
    t = bank.title(story)
    title = t if len(t) <= 85 else t[:82] + "..."
    title += " #shorts"
    description = (f"{t}\n\nWould you survive in this world? Comment below!\n"
                   "New weird world every day - subscribe!\n\n#shorts #story #animation #inthisworld")
    tags = ["in this world", "in this town", "story", "animation", "shorts story", "what if", "W"]
    return title, description, tags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--id", default=None)
    ap.add_argument("--privacy", default=os.environ.get("YT_PRIVACY", "public"))
    args = ap.parse_args()
    seed = args.seed if args.seed is not None else int(time.time())

    stories, errors = bank.load()
    for e in errors:
        print("story problem:", e)
    if not stories:
        raise SystemExit("no stories in the bank")
    story = pick_story(stories, seed, args.id)
    final, _ = make_video(story, seed)
    title, description, tags = youtube_text(story)
    print("title:", title)

    video_id = None
    if args.post:
        if not upload.have_credentials():
            raise SystemExit("Missing YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN - not uploading.")
        video_id = upload.upload(final, title, description, tags, args.privacy)
        print(f"posted: https://youtube.com/shorts/{video_id}")

    if not args.id:
        h = load_history()
        h.setdefault("stories_done", []).append(story["id"])
        if video_id:
            h.setdefault("posted", []).append({"id": video_id, "title": title})
            h["posted"] = h["posted"][-300:]
        save_history(h)


if __name__ == "__main__":
    main()
