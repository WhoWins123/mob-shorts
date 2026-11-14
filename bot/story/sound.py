"""
Narration (edge-tts neural voice, with the exact time of every word for the captions),
plus soft original background music and transition sounds for the stories.
"""
import asyncio
import os
import random
import shutil
import subprocess
import wave

import numpy as np

SR = 44100
NARRATORS = ["en-US-AndrewMultilingualNeural", "en-US-ChristopherNeural", "en-US-BrianMultilingualNeural",
             "en-US-GuyNeural"]


def _decode(data_or_path):
    if isinstance(data_or_path, bytes):
        args = ["ffmpeg", "-loglevel", "error", "-i", "pipe:0"]
        inp = data_or_path
    else:
        args = ["ffmpeg", "-loglevel", "error", "-i", data_or_path]
        inp = None
    raw = subprocess.run(args + ["-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], input=inp, capture_output=True,
                         check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def narrate(text, voice, out_dir, name):
    """
    Returns (samples, words) where words = [(word, start_s, end_s)] relative to the clip.
    Uses edge-tts word timings; falls back to espeak-ng with estimated timings.
    """
    try:
        import edge_tts

        async def go():
            audio = bytearray()
            words = []
            comm = edge_tts.Communicate(text, voice, rate="+8%", boundary="WordBoundary")
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    audio.extend(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    s = chunk["offset"] / 1e7
                    words.append((chunk["text"], s, s + chunk["duration"] / 1e7))
            return bytes(audio), words

        audio, words = asyncio.run(go())
        samples = _decode(audio)
        if words:
            return samples, _attach_punctuation(text, words)
        return samples, _estimate(text, len(samples) / SR)
    except Exception as e:
        print(f"edge-tts failed ({e}); trying espeak-ng")
    if shutil.which("espeak-ng"):
        wav = os.path.join(out_dir, f"{name}.wav")
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "160", "-w", wav, text], check=True)
        samples = _decode(wav)
        return samples, _estimate(text, len(samples) / SR)
    # no voice at all: silent beat long enough to read the captions
    dur = max(2.0, len(text.split()) * 0.33)
    return np.zeros(int(dur * SR), dtype=np.float32), _estimate(text, dur)


def _attach_punctuation(text, words):
    """edge-tts reports bare words; put the punctuation back so captions read naturally."""
    tokens = text.split()
    out, ti = [], 0
    for w, s, e in words:
        shown = w
        for j in range(ti, min(ti + 3, len(tokens))):
            if tokens[j].strip(".,!?\"'…:;-").lower() == w.strip(".,!?\"'…:;-").lower():
                shown = tokens[j]
                ti = j + 1
                break
        out.append((shown, s, e))
    return out


def _estimate(text, dur):
    tokens = text.split()
    weights = [max(2, len(t)) for t in tokens]
    total = sum(weights) or 1
    t, out = 0.0, []
    for tok, w in zip(tokens, weights):
        d = dur * w / total
        out.append((tok, t, t + d))
        t += d
    return out


# ------------------------------------------------------------------ music + sfx

def _tri(freq, n):
    t = np.arange(n) / SR
    return (2 * np.abs(2 * ((t * freq) % 1) - 1) - 1).astype(np.float32)


def _note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def music(seconds, seed, mood="mystery"):
    """Soft original loop: pad chords + gentle arpeggio + light beat."""
    rng = random.Random(seed)
    bpm = rng.choice([84, 92, 100])
    beat = 60 / bpm
    root = rng.choice([45, 47, 48, 50])
    minor = mood != "happy"
    third = 3 if minor else 4
    prog = rng.choice([[0, 8, 3, 10], [0, 5, 8, 7], [0, 3, 8, 7]] if minor else [[0, 5, 7, 5], [0, 9, 5, 7]])
    n_total = int(seconds * SR)
    out = np.zeros(n_total, dtype=np.float32)
    bar = int(beat * 4 * SR)
    eighth = bar // 8
    for b in range(n_total // bar + 1):
        pos = b * bar
        if pos >= n_total:
            break
        root_b = root + prog[b % len(prog)]
        n = min(bar, n_total - pos)
        env = np.minimum(1, np.arange(n) / (SR * 0.3)) * np.minimum(1, (n - np.arange(n)) / (SR * 0.3))
        pad = sum(_tri(_note(root_b + 12 + iv), n) for iv in (0, third, 7)) / 3
        out[pos:pos + n] += pad * env * 0.13
        out[pos:pos + n] += _tri(_note(root_b), n) * env * 0.12
        for k in range(8):  # arpeggio
            p = pos + k * eighth
            m = min(eighth, n_total - p)
            if m <= 0:
                break
            note = root_b + 24 + [0, third, 7, 12, 7, third, 0, 7][k]
            e = np.exp(-np.arange(m) / (SR * 0.18)).astype(np.float32)
            out[p:p + m] += _tri(_note(note), m) * e * 0.07
            if k % 4 == 0:  # soft kick
                kk = min(int(0.1 * SR), m)
                t = np.arange(kk) / SR
                out[p:p + kk] += (np.sin(2 * np.pi * (55 + 60 * np.exp(-t * 30)) * t) * np.exp(-t * 28) * 0.35).astype(np.float32)
    return out


def sfx(kind, rng):
    if kind == "whoosh":
        n = int(0.35 * SR)
        t = np.arange(n) / SR
        noise = rng.uniform(-1, 1, n)
        noise = np.convolve(noise, np.ones(12) / 12, mode="same")
        return (noise * np.sin(np.pi * t / 0.35) * 0.5).astype(np.float32)
    if kind == "ding":
        n = int(0.6 * SR)
        t = np.arange(n) / SR
        return ((np.sin(2 * np.pi * 1320 * t) + 0.5 * np.sin(2 * np.pi * 1980 * t)) * np.exp(-t * 6) * 0.25).astype(np.float32)
    if kind == "boom":
        n = int(0.8 * SR)
        t = np.arange(n) / SR
        noise = np.convolve(rng.uniform(-1, 1, n), np.ones(50) / 50, mode="same")
        return (noise * np.exp(-t * 5) * 2.5 + np.sin(2 * np.pi * 48 * t) * np.exp(-t * 6) * 0.6).astype(np.float32)
    if kind == "pop":
        n = int(0.12 * SR)
        t = np.arange(n) / SR
        return (np.sin(2 * np.pi * (500 + 1500 * t) * t) * np.exp(-t * 30) * 0.4).astype(np.float32)
    return None


def mix(total, voice_clips, events, seed, out_wav, mood="mystery"):
    """voice_clips: [(start, samples)]; events: [(time, sfx_kind)]."""
    rng = np.random.default_rng(seed)
    n = int(total * SR) + SR // 2
    voice = np.zeros(n, dtype=np.float32)
    fx = np.zeros(n, dtype=np.float32)
    for t, clip in voice_clips:
        s = int(t * SR)
        e = min(n, s + len(clip))
        voice[s:e] += clip[:e - s]
    for t, kind in events:
        clip = sfx(kind, rng)
        if clip is None:
            continue
        s = int(t * SR)
        e = min(n, s + len(clip))
        fx[s:e] += clip[:e - s]
    mus = music(total + 1, seed, mood)[:n]
    mus = np.pad(mus, (0, n - len(mus)))
    talking = np.convolve((np.abs(voice) > 0.02).astype(np.float32), np.ones(SR // 4) / (SR // 4), mode="same")
    out = mus * (1 - 0.5 * np.clip(talking * 3, 0, 1)) + fx * 0.6 + voice * 1.1
    fade = int(SR * 0.6)
    out[-fade:] *= np.linspace(1, 0, fade)
    peak = float(np.max(np.abs(out))) or 1.0
    out = out / max(1.0, peak / 0.95)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
