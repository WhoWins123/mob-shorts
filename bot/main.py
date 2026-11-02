"""
Makes one Short from start to finish and (optionally) posts it.

    python -m bot.main            # make a video into out/ (no upload)
    python -m bot.main --post     # make it and upload it to YouTube
"""
import argparse
import os
import subprocess
import time

from . import audio, matchups, render, upload
from .assets import Textures
from .mobs import ROSTER
from .sim import FPS, Battle
from .sprites import Sprites

INTRO = 2.6          # seconds of lineup before the fight
OUT = os.path.join(os.path.dirname(__file__), "..", "out")


def make_video(seed: int):
    os.makedirs(OUT, exist_ok=True)
    print(f"seed {seed}")
    textures = Textures.load()
    sprites = Sprites(textures)
    pool = sprites.prepare(ROSTER)
    if sprites.missing:
        print("skipping mobs whose texture changed/missing:", ", ".join(sprites.missing))
    # Try a few matchups and keep the closest, most watchable fight: not too short,
    # not a draw, and the winner shouldn't have most of its team left.
    best = None
    for attempt in range(14):
        s = seed + attempt * 7919
        m = matchups.pick(pool, s)
        result = Battle(m.team_a, m.team_b, s).run()
        fight_len = len(result.frames) / FPS
        size = result.team_size[result.winner] if result.winner >= 0 else 1
        left = len(result.survivors) / size
        score = (fight_len < 9 or fight_len > 44) * 10 + (result.winner < 0) * 10 + max(0, left - 0.5) * 5
        if best is None or score < best[0]:
            best = (score, m, result, fight_len)
        if score == 0:
            break
    _, m, result, fight_len = best
    print("matchup:", m.title)
    winner_label = None if result.winner < 0 else (m.label_a if result.winner == 0 else m.label_b)
    print(f"fight {fight_len:.1f}s, winner: {winner_label or 'draw'}")

    # ---- voiceover
    voice_name = audio.VOICES[seed % len(audio.VOICES)]
    voices = []
    intro_clip = audio.speak(m.intro_line, OUT, "intro", voice_name)
    if intro_clip is not None:
        voices.append((0.25, intro_clip))
    if result.last_stand:
        t, team, mob = result.last_stand
        line = f"Only one {mob.name.lower()} left!"
        if INTRO + t + 2.5 < INTRO + fight_len:
            clip = audio.speak(line, OUT, "mid", voice_name)
            if clip is not None:
                voices.append((INTRO + t + 0.2, clip))
    if winner_label:
        team_word = winner_label.split(" ", 1)[1].lower()
        end_line = f"The {team_word} win! Comment which mobs should fight next."
    else:
        end_line = "It's a draw! Nobody survived. Comment which mobs should fight next."
    end_clip = audio.speak(end_line, OUT, "end", voice_name)
    end_len = 3.2 if end_clip is None else max(3.2, len(end_clip) / audio.SR + 0.9)
    if end_clip is not None:
        voices.append((INTRO + fight_len + 0.3, end_clip))
    total = INTRO + fight_len + end_len

    # ---- video
    r = render.Renderer(sprites, textures, m)
    first, last = result.frames[0], result.frames[-1]

    def frames():
        for i in range(int(INTRO * FPS)):
            yield r.frame_intro(first, i / FPS, INTRO)
        for snap in result.frames:
            yield r.frame_fight(snap)
        for i in range(int(end_len * FPS)):
            yield r.frame_end(last, i / FPS, result.winner, result.survivors)

    silent = os.path.join(OUT, "video_silent.mp4")
    started = time.time()
    n = render.encode(frames(), silent)
    print(f"rendered {n} frames in {time.time() - started:.0f}s")

    # ---- audio + mux
    events = [(INTRO + t, kind) for t, kind, _ in result.events]
    wav = os.path.join(OUT, "audio.wav")
    audio.mix(total, events, voices, seed, wav)
    final = os.path.join(OUT, "short.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", final], check=True)
    print("video:", final, f"({total:.1f}s)")
    return final, m, winner_label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true", help="upload to YouTube")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--privacy", default=os.environ.get("YT_PRIVACY", "public"))
    args = ap.parse_args()
    seed = args.seed if args.seed is not None else int(time.time())

    final, m, winner_label = make_video(seed)
    title, description, tags = matchups.youtube_text(m, winner_label)
    print("title:", title)

    video_id = None
    if args.post:
        if not upload.have_credentials():
            raise SystemExit("Missing YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN secrets - not uploading.")
        video_id = upload.upload(final, title, description, tags, args.privacy)
        print(f"posted: https://youtube.com/shorts/{video_id}")
    matchups.remember(m, video_id)


if __name__ == "__main__":
    main()
