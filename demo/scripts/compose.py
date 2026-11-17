"""Composes the video following skill-video: cover, steps with side panel and checklist,
recording card, smooth zoom, 0.35 s crossfade cuts and closing card."""
import subprocess, math, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
RW, RH = 1440, 900
REC = "build/recording.mp4"
FD = "/usr/share/fonts/opentype/inter/"
NAMES = {200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold"}
_fc = {}
def F(w, s):
    if (w, s) not in _fc: _fc[(w, s)] = ImageFont.truetype(FD + f"Inter-{NAMES[w]}.otf", s)
    return _fc[(w, s)]

BRAND = np.array([79, 70, 229], float)

# ---------- background (solid brand color + dot pattern) ----------
def make_bg():
    # solid brand color, no gradient
    im = Image.new("RGBA", (W, H), tuple(int(c) for c in BRAND) + (255,))
    dots = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(dots)
    for y in range(24, H, 48):
        for x in range(24, W, 48):
            dd.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 255, 255, int(255 * 0.16)))
    return Image.alpha_composite(im, dots)

BG = make_bg()

CREDIT_TEXT = "Made by @mauribeza  ·  github.com/mauribeza"

def ease(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def ease_io(u):  # smooth curve (cubic in-out)
    u = max(0.0, min(1.0, u)); return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
def back(u):
    u = max(0.0, min(1.0, u)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2

def layer(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))

def paste_a(base, img, xy, alpha):
    if alpha <= 0: return
    if alpha < 1:
        a = img.getchannel("A").point(lambda v: int(v * alpha)); img = img.copy(); img.putalpha(a)
    base.alpha_composite(img, (int(xy[0]), int(xy[1])))

def text_img(txt, font, fill=(255, 255, 255, 255), spacing=0):
    if spacing:
        w = sum(font.getlength(c) + spacing for c in txt)
    else:
        w = font.getlength(txt)
    asc, desc = font.getmetrics()
    im = layer((int(w) + 4, asc + desc + 4)); d = ImageDraw.Draw(im)
    if spacing:
        x = 0
        for c in txt: d.text((x, 0), c, font=font, fill=fill); x += font.getlength(c) + spacing
    else:
        d.text((0, 0), txt, font=font, fill=fill)
    return im

def pill(txt, size=15):
    t = text_img(txt, F(700, size), spacing=2.5)
    w, h = t.width + 36, size + 22
    im = layer((w + 2, h + 2)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((1, 1, w, h), h // 2, outline=(255, 255, 255, 170), width=2, fill=(255, 255, 255, 22))
    im.alpha_composite(t, (19, (h - t.height) // 2 + 3))
    return im

def logo(scale=1.0):
    s = int(56 * scale)
    t = text_img("Taskflow", F(800, int(40 * scale)))
    im = layer((s + 16 + t.width, max(s, t.height))); d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, s - 2, s - 2), int(14 * scale), outline="white", width=max(3, int(4 * scale)))
    d.line((s * .28, s * .52, s * .44, s * .68, s * .72, s * .34), fill="white", width=max(4, int(5 * scale)))
    im.alpha_composite(t, (s + 16, (s - t.height) // 2 + 2))
    return im

def wrap(txt, font, width):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= width: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

CREDIT = text_img(CREDIT_TEXT, F(500, 20), fill=(255, 255, 255, 190))

# ---------- cover / closing ----------
def title_card(kind, out, dur):
    if kind == "cover":
        p, t1, t2, sub = "TUTORIAL", "Getting", "Started", "Create, track and filter tasks in Taskflow"
    else:
        p, t1, t2, sub = "TASKFLOW", "Thank", "You", "You're ready to run your board with Taskflow."
    lg = logo(1.0); pl = pill(p)
    a = text_img(t1, F(800, 120)); b = text_img(" " + t2, F(200, 120))
    title = layer((a.width + b.width, a.height)); title.alpha_composite(a, (0, 0)); title.alpha_composite(b, (a.width, 0))
    line = layer((90, 4)); ImageDraw.Draw(line).rounded_rectangle((0, 0, 89, 3), 2, fill=(255, 255, 255, 220))
    st = text_img(sub, F(400, 30), fill=(255, 255, 255, 220))
    els = [(lg, 300), (pl, 400), (title, 458), (line, 630), (st, 664), (CREDIT, 990)]
    enc = encoder(out)
    n = int(round(dur * FPS))
    for i in range(n):
        t = i / FPS
        fr = BG.copy()
        out_u = ease((t - (dur - 0.6)) / 0.6) if kind == "cover" else 0
        for k, (im, y) in enumerate(els):
            u = ease((t - 0.15 - k * 0.14) / 0.55)
            alpha = u * (1 - out_u)
            dy = (1 - u) * 26 - out_u * 40
            paste_a(fr, im, ((W - im.width) / 2, y + dy), alpha)
        enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait()

# ---------- steps ----------
CARD_W = 1256; PAD = 8
REC_W = CARD_W - 2 * PAD; REC_H = round(REC_W * RH / RW)
CARD_H = REC_H + 2 * PAD
CX = W - 72 - CARD_W; CY = (H - CARD_H) // 2

def card_base():
    base = BG.copy()
    sh = layer((W, H)); ImageDraw.Draw(sh).rounded_rectangle((CX, CY + 18, CX + CARD_W, CY + CARD_H + 18), 22, fill=(10, 8, 40, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    base.alpha_composite(sh)
    ImageDraw.Draw(base).rounded_rectangle((CX, CY, CX + CARD_W, CY + CARD_H), 22, fill="white")
    base.alpha_composite(CREDIT, (72, H - 72 - CREDIT.height // 2))
    return base

CARD_BASE = card_base()
MASK = Image.new("L", (REC_W, REC_H), 0)
ImageDraw.Draw(MASK).rounded_rectangle((0, 0, REC_W - 1, REC_H - 1), 15, fill=255)

def later_label():
    t = text_img("A few minutes later", F(600, 19))
    w, h = t.width + 64, 44
    im = layer((w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=(15, 23, 42, 225))
    d.ellipse((16, 12, 36, 32), outline="white", width=2)
    d.line((26, 16, 26, 22, 31, 25), fill="white", width=2)
    im.alpha_composite(t, (46, (h - t.height) // 2 + 2))
    return im
LATER = later_label()

def panel_elements(n, t1, t2, desc, items, note):
    els = []
    els.append((pill(f"STEP {n}"), 72, 176))
    a = text_img(t1, F(800, 64)); b = text_img(t2, F(200, 64))
    els.append((a, 70, 224)); els.append((b, 70, 296))
    dl = wrap(desc, F(400, 23), 470)
    dim = layer((480, 34 * len(dl))); dd = ImageDraw.Draw(dim)
    for i, l in enumerate(dl): dd.text((0, i * 34), l, font=F(400, 23), fill=(255, 255, 255, 215))
    els.append((dim, 72, 388))
    hy = 388 + 34 * len(dl) + 38
    els.append((text_img("HOW IT WORKS", F(700, 14), fill=(255, 255, 255, 170), spacing=2.5), 72, hy))
    iy = hy + 38; rows = []
    for k, it in enumerate(items):
        y = iy + k * 54
        im = layer((480, 40)); d = ImageDraw.Draw(im)
        d.ellipse((1, 4, 31, 34), outline=(255, 255, 255, 150), width=2)
        d.text((48, 7), it, font=F(600, 20), fill=(255, 255, 255, 235))
        els.append((im, 72, y)); rows.append(y)
    ny = iy + len(items) * 54 + 22
    nl = wrap(note, F(400, 18), 430)
    nim = layer((480, 36 + 26 * len(nl))); nd = ImageDraw.Draw(nim)
    nd.rounded_rectangle((0, 0, 479, nim.height - 1), 14, fill=(255, 255, 255, 30), outline=(255, 255, 255, 70), width=1)
    for i, l in enumerate(nl): nd.text((22, 18 + i * 26), l, font=F(400, 18), fill=(255, 255, 255, 225))
    els.append((nim, 72, ny))
    return els, rows

def draw_check(fr, y, u):
    s = back(u)
    r = 15 * s
    cx, cy = 72 + 16, y + 19
    o = layer((W, H)) if False else None
    d = ImageDraw.Draw(fr)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255))
    if u > 0.25:
        k = min(1, (u - 0.25) / 0.5)
        p1, p2, p3 = (cx - 7, cy), (cx - 2, cy + 6), (cx + 8, cy - 6)
        pts = [p1, p2] if k < 0.4 else [p1, p2, (p2[0] + (p3[0] - p2[0]) * (k - 0.4) / 0.6, p2[1] + (p3[1] - p2[1]) * (k - 0.4) / 0.6)]
        if k < 0.4: pts = [p1, (p1[0] + (p2[0] - p1[0]) * k / 0.4, p1[1] + (p2[1] - p1[1]) * k / 0.4)]
        d.line(pts, fill=tuple(int(c) for c in BRAND), width=4, joint="curve")

class Reader:
    def __init__(self, t0, t1):
        self.n = int(round((t1 - t0) * FPS)); self.i = -1; self.cur = None
        self.p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", f"{t0:.3f}", "-i", REC, "-t", f"{t1 - t0:.3f}",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    def get(self, k):
        k = min(k, self.n - 1)
        while self.i < k:
            b = self.p.stdout.read(RW * RH * 3)
            if len(b) < RW * RH * 3: break
            self.cur = np.frombuffer(b, np.uint8).reshape(RH, RW, 3); self.i += 1
        return self.cur

FULL = (0, 0, RW, RH)
def region(cx, cy, w):
    h = w * RH / RW
    x0 = min(max(cx - w / 2, 0), RW - w); y0 = min(max(cy - h / 2, 0), RH - h)
    return (x0, y0, w, h)

def zoom_at(t, keys):
    """keys: list of (t0, t1, region_from, region_to); the region is held outside those ranges."""
    r = keys[0][2] if keys else FULL
    for t0, t1, a, b in keys:
        if t >= t1: r = b
        elif t >= t0:
            u = ease_io((t - t0) / (t1 - t0))
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(4))
    return r

def render_step(cfg, out):
    els, rows = panel_elements(cfg["n"], cfg["t1"], cfg["t2"], cfg["desc"], cfg["items"], cfg["note"])
    segs = cfg["segs"]  # [(raw0, raw1, fade_in)]
    starts, t = [], 0.0
    for k, (a, b, fade) in enumerate(segs):
        if k and fade: t -= 0.35
        starts.append(t); t += b - a
    dur = t
    readers = [None] * len(segs)
    enc = encoder(out)
    static = None
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        fr = CARD_BASE.copy()
        # panel with staggered entrance
        if t < 1.6:
            for k, (im, x, y) in enumerate(els):
                u = ease((t - 0.1 - k * 0.07) / 0.45)
                paste_a(fr, im, (x, y + (1 - u) * 18), u)
        else:
            if static is None:
                static = layer((W, H))
                for im, x, y in els: static.alpha_composite(im, (x, y))
            fr.alpha_composite(static)
        for y, tc in zip(rows, cfg["checks"]):
            if t >= tc: draw_check(fr, y, (t - tc) / 0.45)
        # recording
        reg = zoom_at(t, cfg.get("zoom", []))
        frames = []
        for k, (a, b, fade) in enumerate(segs):
            s0, s1 = starts[k], starts[k] + (b - a)
            if s0 <= t < s1 or (k == len(segs) - 1 and t >= s0):
                if readers[k] is None: readers[k] = Reader(a, b)
                alpha = 1.0
                if k and segs[k][2] and t < s0 + 0.35: alpha = ease((t - s0) / 0.35)
                frames.append((readers[k].get(int((t - s0) * FPS)), alpha))
        img = None
        for arr, al in frames:
            x0, y0, w, h = reg
            cur = Image.fromarray(arr).resize((REC_W, REC_H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
            img = cur if img is None else Image.blend(img, cur, al)
        fr.paste(img, (CX + PAD, CY + PAD), MASK)
        lt = cfg.get("later")
        if lt is not None and lt <= t < lt + 2.2:
            a = min(1, (t - lt) / 0.3, (lt + 2.2 - t) / 0.3)
            paste_a(fr, LATER, (CX + CARD_W - 28 - LATER.width, CY + 28), a)
        enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait()
    return dur

def encoder(path):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                             "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)

MODAL = region(720, 470, 1024)
WORK2 = region(950, 420, 960)
WORK3 = region(760, 440, 1000)

STEPS = [
    dict(n=1, t1="Create", t2="a task", desc="Add a new task to your board in just a few seconds.",
         items=["Click New task", "Type a clear title", "Set priority and due date", "Click Create task"],
         note="New tasks land in the To do column.",
         segs=[(2.8, 5.6, False), (8.6, 13.0, True), (13.6, 17.4, True), (21.5, 25.3, True)],
         checks=[2.6, 6.4, 9.5, 10.45],
         zoom=[(2.75, 3.75, FULL, MODAL), (10.75, 11.75, MODAL, FULL)]),
    dict(n=2, t1="Track", t2="progress", desc="Move each card across the board as the work moves forward.",
         items=["Drag the card to In progress", "Complete its subtasks", "Drop it in Done"],
         note="Progress bars fill up as subtasks are checked off.",
         segs=[(26.3, 31.8, False), (183.0, 189.0, True)],
         checks=[3.8, 5.6, 10.05], later=5.15,
         zoom=[(5.6, 6.6, FULL, WORK2), (9.95, 10.95, WORK2, FULL)]),
    dict(n=3, t1="Filter", t2="the board", desc="Focus only on the work that matters to you right now.",
         items=["Open Filter", "Choose Assigned to me", "Review your tasks"],
         note="Remove the chip to see the whole board again.",
         segs=[(194.3, 200.0, False), (200.0, 205.5, False)],
         checks=[1.3, 2.6, 3.9],
         zoom=[(3.0, 4.0, FULL, WORK3), (8.6, 9.6, WORK3, FULL)]),
]

if __name__ == "__main__":
    which = sys.argv[1:] or ["cover", "1", "2", "3", "closing"]
    durs = {}
    for w in which:
        if w == "cover": title_card("cover", "build/cover.mp4", 3.0)
        elif w == "closing": title_card("closing", "build/closing.mp4", 5.0)
        else: durs[w] = render_step(STEPS[int(w) - 1], f"build/step{w}.mp4")
    print(json.dumps(durs))
