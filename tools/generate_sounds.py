"""
Génère les sons du jeu (WAV 22 kHz, synthèse maison) dans assets/sounds/.

    python tools/generate_sounds.py

Vous pouvez remplacer n'importe quel fichier par le vôtre (même nom, .wav ou .ogg) :
    step, push, bump, target, undo, click, win, music
"""
import math
import random
import struct
import wave
from pathlib import Path

SR = 22050
OUT = Path(__file__).resolve().parent.parent / "assets" / "sounds"


def save(name, samples, volume=0.8):
    OUT.mkdir(parents=True, exist_ok=True)
    peak = max(1e-9, max(abs(s) for s in samples))
    with wave.open(str(OUT / f"{name}.wav"), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(32767 * volume * s / peak)) for s in samples))


def env(i, n, attack=0.01, release=0.6):
    t = i / n
    a = min(1.0, t / max(attack, 1e-6))
    r = min(1.0, (1 - t) / max(release, 1e-6))
    return a * r


def tone(freq, dur, wave_="square", vol=1.0, decay=3.0, slide=0.0):
    n = int(SR * dur)
    out, ph = [], 0.0
    for i in range(n):
        f = freq * (1 + slide * i / n)
        ph += f / SR
        x = ph % 1.0
        if wave_ == "square":
            v = 1.0 if x < 0.5 else -1.0
        elif wave_ == "tri":
            v = 4 * abs(x - 0.5) - 1
        elif wave_ == "saw":
            v = 2 * x - 1
        else:
            v = math.sin(2 * math.pi * x)
        out.append(v * vol * math.exp(-decay * i / n) * min(1.0, i / 80))
    return out


def noise(dur, vol=1.0, decay=8.0, lowpass=0.3):
    rnd, n, y, out = random.Random(7), int(SR * dur), 0.0, []
    for i in range(n):
        y += lowpass * (rnd.uniform(-1, 1) - y)
        out.append(y * vol * math.exp(-decay * i / n))
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


def seq(notes, gap=0.0):
    out = []
    for s in notes:
        out += s + [0.0] * int(SR * gap)
    return out


def note(m):  # numéro MIDI -> Hz
    return 440 * 2 ** ((m - 69) / 12)


def music():
    """Ambiance de donjon : bourdon grave + arpège lent mineur + petites notes de cloche."""
    bpm, beat = 66, 60 / 66
    bars = 8
    dur = bars * 4 * beat
    n = int(SR * dur)
    out = [0.0] * n
    prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (43, [55, 59, 62]), (40, [52, 55, 59])]  # Am F G Em
    rnd = random.Random(3)
    for bar in range(bars):
        root, chord = prog[bar % 4]
        t0 = bar * 4 * beat
        # bourdon
        d = tone(note(root - 12), 4 * beat, "tri", 0.55, 0.6)
        d2 = tone(note(root - 12) * 1.003, 4 * beat, "sine", 0.4, 0.6)
        for i, v in enumerate(mix(d, d2)):
            j = int(t0 * SR) + i
            if j < n:
                out[j] += v * env(i, len(d), 0.1, 0.3)
        # arpège (croche)
        for k in range(8):
            m = chord[(k if k < 4 else 7 - k) % 3] + (12 if k % 4 == 3 else 0)
            s = tone(note(m), 0.6 * beat, "tri", 0.30, 3.5)
            for i, v in enumerate(s):
                j = int((t0 + k * beat / 2) * SR) + i
                if j < n:
                    out[j] += v
        # cloche aléatoire
        if bar % 2 == 1:
            m = rnd.choice(chord) + 24
            s = mix(tone(note(m), 1.6 * beat, "sine", 0.22, 2.2), tone(note(m) * 2.76, 1.0 * beat, "sine", 0.06, 4.0))
            for i, v in enumerate(s):
                j = int((t0 + 2.5 * beat) * SR) + i
                if j < n:
                    out[j] += v
    # petite réverbération (écho doux)
    for delay, g in ((int(SR * 0.28), 0.35), (int(SR * 0.53), 0.2)):
        for i in range(n - 1, delay - 1, -1):
            out[i] += out[i - delay] * g
    # fondu pour boucler proprement
    f = int(SR * 0.05)
    for i in range(f):
        out[i] *= i / f
        out[n - 1 - i] *= i / f
    return out


def main():
    save("step", mix(noise(0.06, 0.5, 14, 0.18), tone(110, 0.05, "tri", 0.5, 9)), 0.45)
    save("push", mix(noise(0.16, 0.9, 6, 0.08), tone(70, 0.16, "saw", 0.5, 7, -0.3)), 0.8)
    save("bump", tone(90, 0.07, "square", 0.6, 12, -0.4), 0.35)
    save("target", seq([tone(note(76), 0.09, "square", 0.5, 4), tone(note(83), 0.22, "square", 0.5, 4)]), 0.5)
    save("undo", tone(500, 0.12, "square", 0.5, 5, -0.5), 0.4)
    save("click", tone(900, 0.04, "square", 0.5, 12), 0.35)
    win = seq([tone(note(m), 0.14, "square", 0.5, 3) for m in (72, 76, 79, 84)]) + \
        mix(tone(note(84), 0.7, "square", 0.4, 3), tone(note(79), 0.7, "tri", 0.4, 3), tone(note(76), 0.7, "tri", 0.4, 3))
    save("win", win, 0.6)
    save("music", music(), 0.5)
    print("Sons générés dans", OUT)


if __name__ == "__main__":
    main()
