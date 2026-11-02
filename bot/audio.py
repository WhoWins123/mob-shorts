"""
Sound for the video: AI voiceover (Microsoft Edge neural voices via edge-tts, with espeak-ng as a
backup), original procedurally generated chiptune music, and simple synthesized sound effects.
Nothing copyrighted is used.
"""
import asyncio
import os
import random
import shutil
import subprocess
import wave

import numpy as np

SR = 44100
VOICES = ["en-US-AndrewMultilingualNeural", "en-US-GuyNeural", "en-US-ChristopherNeural", "en-US-EricNeural"]


# ------------------------------------------------------------------ voice

def _decode(path):
    """Any audio file -> mono float32 at SR."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def speak(text, out_dir, name, voice):
    """Returns the voice clip as samples, or None if no TTS engine is available."""
    mp3 = os.path.join(out_dir, f"{name}.mp3")
    try:
        import edge_tts

        async def go():
            await edge_tts.Communicate(text, voice, rate="+12%", pitch="+0Hz").save(mp3)

        asyncio.run(go())
        return _decode(mp3)
    except Exception as e:  # no network / service changed: fall back to espeak
        print(f"edge-tts failed ({e}); trying espeak-ng")
    if shutil.which("espeak-ng"):
        wav = os.path.join(out_dir, f"{name}.wav")
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "165", "-w", wav, text], check=True)
        return _decode(wav)
    return None


# ------------------------------------------------------------------ music

def _square(freq, n, duty=0.5):
    t = np.arange(n) / SR
    return np.where((t * freq) % 1.0 < duty, 1.0, -1.0).astype(np.float32)


def _note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def music(seconds, seed):
    """A short original chiptune loop: bass + arpeggio + drums, random key and progression."""
    rng = random.Random(seed)
    bpm = rng.choice([140, 150, 160])
    beat = 60 / bpm
    root = rng.choice([45, 47, 48, 50, 52])          # A2..E3
    progs = [[0, 5, 3, 4], [0, 3, 5, 4], [0, 5, 0, 4], [0, -2, 3, 4]]
    prog = rng.choice(progs)
    minor = rng.random() < 0.7
    third = 3 if minor else 4
    n_total = int(seconds * SR)
    out = np.zeros(n_total, dtype=np.float32)
    step = int(beat / 2 * SR)                         # eighth notes
    i = 0
    pos = 0
    scale_steps = [0, 2, 3, 5, 7, 8, 10] if minor else [0, 2, 4, 5, 7, 9, 11]
    while pos < n_total:
        bar = (i // 8) % len(prog)
        degree = prog[bar]
        chord_root = root + (scale_steps[degree % 7] if degree >= 0 else -2)
        n = min(step, n_total - pos)
        env = np.exp(-np.arange(n) / (SR * 0.12)).astype(np.float32)
        # bass on every eighth, octave jump on off-beats
        bass = _square(_note(chord_root + (12 if i % 2 else 0)), n, 0.5) * env * 0.22
        arp_note = chord_root + 24 + [0, third, 7, 12][i % 4]
        arp = _square(_note(arp_note), n, 0.25) * env * 0.11
        out[pos:pos + n] += bass + arp
        # drums: kick on beats, noise hat on off-beats, snare on 2 and 4
        if i % 2 == 0:
            k = min(int(0.12 * SR), n)
            t = np.arange(k) / SR
            out[pos:pos + k] += (np.sin(2 * np.pi * (60 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 25) * 0.5).astype(np.float32)
        else:
            k = min(int(0.04 * SR), n)
            out[pos:pos + k] += (np.random.default_rng(i).uniform(-1, 1, k) * np.exp(-np.arange(k) / (SR * 0.01)) * 0.08).astype(np.float32)
        if i % 4 == 2:
            k = min(int(0.15 * SR), n)
            out[pos:pos + k] += (np.random.default_rng(i + 7).uniform(-1, 1, k) * np.exp(-np.arange(k) / (SR * 0.04)) * 0.18).astype(np.float32)
        pos += step
        i += 1
    return out


# ------------------------------------------------------------------ sound effects

def _sfx(kind, rng):
    if kind == "hit":
        n = int(0.09 * SR)
        t = np.arange(n) / SR
        return (rng.uniform(-1, 1, n) * np.exp(-t * 45) * 0.5 + np.sin(2 * np.pi * 140 * t) * np.exp(-t * 30) * 0.4).astype(np.float32)
    if kind in ("shoot", "arrow_hit"):
        n = int(0.07 * SR)
        t = np.arange(n) / SR
        f = 900 if kind == "shoot" else 300
        return (np.sin(2 * np.pi * f * t * (1 - t * 4)) * np.exp(-t * 50) * 0.3).astype(np.float32)
    if kind in ("fireball", "burn"):
        n = int(0.25 * SR)
        t = np.arange(n) / SR
        return (rng.uniform(-1, 1, n) * np.exp(-t * 12) * 0.3).astype(np.float32)
    if kind == "explosion":
        n = int(0.9 * SR)
        t = np.arange(n) / SR
        noise = rng.uniform(-1, 1, n)
        low = np.convolve(noise, np.ones(40) / 40, mode="same")  # muffled boom
        return (low * np.exp(-t * 4) * 2.2 + np.sin(2 * np.pi * 50 * t) * np.exp(-t * 6) * 0.6).astype(np.float32)
    if kind == "fuse":
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        return (rng.uniform(-1, 1, n) * 0.12 * (1 - t / 0.5)).astype(np.float32)
    if kind == "poof":
        n = int(0.18 * SR)
        t = np.arange(n) / SR
        return (rng.uniform(-1, 1, n) * np.exp(-t * 25) * 0.25).astype(np.float32)
    if kind == "death":
        n = int(0.25 * SR)
        t = np.arange(n) / SR
        return (np.sin(2 * np.pi * (400 - 900 * t) * t) * np.exp(-t * 10) * 0.25).astype(np.float32)
    return None


def _add(track, clip, at_seconds, gain=1.0):
    start = int(at_seconds * SR)
    if clip is None or start >= len(track):
        return
    end = min(len(track), start + len(clip))
    track[start:end] += clip[:end - start] * gain


def mix(total_seconds, events, voices, seed, out_wav):
    """events: (time, kind) for sfx; voices: (time, samples) clips. Music ducks under the voice."""
    rng = np.random.default_rng(seed)
    n = int(total_seconds * SR) + SR
    sfx = np.zeros(n, dtype=np.float32)
    voice = np.zeros(n, dtype=np.float32)
    last = {}
    for t, kind in events:
        if t - last.get(kind, -1) < 0.06:  # don't stack dozens of identical sounds
            continue
        last[kind] = t
        _add(sfx, _sfx(kind, rng), t, 0.6)
    for t, clip in voices:
        _add(voice, clip, t, 1.0)

    mus = music(total_seconds + 1, seed)[:n]
    mus = np.pad(mus, (0, n - len(mus)))
    # duck the music while someone is talking
    talking = np.convolve(np.abs(voice) > 0.02, np.ones(SR // 5) / (SR // 5), mode="same")
    duck = 1.0 - 0.65 * np.clip(talking * 3, 0, 1)
    out = mus * 0.55 * duck + sfx * 0.7 + voice * 1.0
    # fade out the last second, keep it from clipping
    fade = int(SR * 0.8)
    out[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(out)) or 1
    out = out / max(1.0, peak / 0.95)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
