"""Música original instrumental (numpy/scipy): pads, arpegio, bajo, percusión
sutil y reverb, ~90 BPM, progresión optimista I–V–vi–IV en Do mayor."""
import subprocess, numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, lfilter

SR = 44100
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            "build/video.mp4"], capture_output=True, text=True).stdout)
N = int(round(dur * SR)); t = np.arange(N) / SR
BPM = 90; beat = 60 / BPM; bar = 4 * beat
rng = np.random.default_rng(7)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
CHORDS = [[60, 64, 67, 71], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]]  # Cmaj7 G Am F
BASS = [36, 31, 33, 29]
out = np.zeros((N, 2))

def env(n, a, r):
    e = np.ones(n); ai = int(a * SR); ri = int(r * SR)
    e[:ai] = np.linspace(0, 1, ai); e[-ri:] *= np.linspace(1, 0, ri); return e

def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR); j = min(N, i + len(sig))
    if j <= i: return
    s = sig[:j - i] * gain
    out[i:j, 0] += s * (1 - pan) / 2 * 2 ** .5; out[i:j, 1] += s * (1 + pan) / 2 * 2 ** .5

nbars = int(np.ceil(dur / bar)) + 1
for b in range(nbars):
    st = b * bar; ch = CHORDS[b % 4]
    n = int((bar + 1.0) * SR); tt = np.arange(n) / SR
    pad = np.zeros(n)
    for m in ch:
        for det in (-0.12, 0.12):
            f = hz(m) * 2 ** (det / 12)
            pad += np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)
    add(pad * env(n, 0.9, 1.0) * 0.035, st)
    # bajo suave
    for k in (0, 2):
        n2 = int(beat * 2 * SR); tt2 = np.arange(n2) / SR
        f = hz(BASS[b % 4])
        add((np.sin(2 * np.pi * f * tt2) + 0.2 * np.sin(4 * np.pi * f * tt2)) * env(n2, 0.02, 0.4) * 0.16, st + k * beat)
    # arpegio ligero (corcheas)
    arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12]
    for k, m in enumerate(arp):
        n3 = int(0.6 * SR); tt3 = np.arange(n3) / SR
        f = hz(m)
        tone = (np.sin(2 * np.pi * f * tt3) + 0.25 * np.sin(6 * np.pi * f * tt3)) * np.exp(-tt3 * 7)
        add(tone * 0.05, st + k * beat / 2, pan=0.35 if k % 2 else -0.35)
    # percusión sutil
    for k in range(4):
        n4 = int(0.25 * SR); tt4 = np.arange(n4) / SR
        kick = np.sin(2 * np.pi * (55 + 70 * np.exp(-tt4 * 30)) * tt4) * np.exp(-tt4 * 18)
        add(kick * (0.22 if k in (0, 2) else 0.0), st + k * beat)
        hat = rng.standard_normal(int(0.05 * SR)) * np.exp(-np.arange(int(0.05 * SR)) / SR * 90)
        bb, aa = butter(2, 7000 / (SR / 2), "high"); hat = lfilter(bb, aa, hat)
        add(hat * 0.03, st + k * beat + beat / 2, pan=0.2)
        if k in (1, 3):
            n5 = int(0.18 * SR); sn = rng.standard_normal(n5) * np.exp(-np.arange(n5) / SR * 25)
            bb, aa = butter(2, [900 / (SR / 2), 5000 / (SR / 2)], "band"); add(lfilter(bb, aa, sn) * 0.05, st + k * beat)

# reverb (respuesta al impulso sintética)
ir_n = int(2.2 * SR); ir_t = np.arange(ir_n) / SR
wet = np.zeros_like(out)
for c in range(2):
    ir = rng.standard_normal(ir_n) * np.exp(-ir_t * 2.6); ir[0] = 0
    wet[:, c] = fftconvolve(out[:, c], ir)[:N] * 0.018
mix = out * 0.8 + wet
fi, fo = int(1.5 * SR), int(3.5 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix /= np.abs(mix).max() / 0.8
sf.write("build/music.wav", mix.astype(np.float32), SR)
print("music", len(mix) / SR, "video", dur)
