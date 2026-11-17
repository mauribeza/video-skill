"""Generates a synthetic screen recording of a fictional app ("Taskflow") to test
skill-video. It deliberately includes dead time, a loading spinner, an error
toast, an unnecessary detour and a jump of several minutes."""
import subprocess, math, os
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1440, 900, 30
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def F(w, s):
    k = (w, s)
    if k not in _fc:
        name = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold"}[w]
        _fc[k] = ImageFont.truetype(FD + f"Inter-{name}.otf", s)
    return _fc[k]

INDIGO = (79, 70, 229)
CARDS = {
    "notes":   ("Write release notes", "Docs", (14, 116, 144), "AR", "Nov 18", None),
    "pricing": ("Update pricing page", "Web", (190, 24, 93), "JL", "Nov 19", None),
    "qa":      ("QA mobile build", "QA", (180, 83, 9), "AR", "Nov 21", None),
    "onb":     ("Design onboarding flow", "Design", (109, 40, 217), "MK", "Nov 17", (2, 4)),
    "api":     ("API rate limits", "Backend", (21, 128, 61), "AR", "Nov 22", (1, 3)),
    "kick":    ("Kickoff meeting", "Ops", (71, 85, 105), "JL", "Nov 10", None),
    "research":("Competitive research", "Research", (3, 105, 161), "MK", "Nov 12", None),
    "demo":    ("Prepare client demo", "Sales", (220, 38, 38), "AR", "Nov 20", (0, 3)),
}
AV = {"AR": (79, 70, 229), "JL": (219, 39, 119), "MK": (5, 150, 105)}
COLX = [264, 652, 1040]; COLW = 368; COLY = 170
CW, CH, CGAP = 336, 108, 12
COLNAMES = ["To do", "In progress", "Done"]

def card_pos(ci, idx, filt=False):
    y0 = COLY + (52 if not filt else 92)
    return COLX[ci] + 16, y0 + idx * (CH + CGAP)

def draw_card(d, x, y, cid, sub=None, done=False, hl=0.0):
    title, tag, tc, who, due, st = CARDS[cid]
    if sub is not None: st = sub
    border = tuple(int(229 + (c - 229) * hl) for c in (INDIGO[0], INDIGO[1], INDIGO[2])) if hl > 0 else (226, 232, 240)
    d.rounded_rectangle((x, y, x + CW, y + CH), 12, fill="white", outline=border, width=2 if hl > 0 else 1)
    tw = d.textlength(tag, font=F(600, 12)) + 20
    tint = tuple(int(255 - (255 - c) * 0.14) for c in tc)
    d.rounded_rectangle((x + 16, y + 14, x + 16 + tw, y + 36), 11, fill=tint)
    d.text((x + 26, y + 17), tag, font=F(600, 12), fill=tc)
    if cid == "demo":
        d.rounded_rectangle((x + 24 + tw, y + 14, x + 24 + tw + 50, y + 36), 11, fill=(254, 226, 226))
        d.text((x + 34 + tw, y + 17), "High", font=F(600, 12), fill=(185, 28, 28))
    if done:
        d.ellipse((x + CW - 38, y + 12, x + CW - 14, y + 36), fill=(22, 163, 74))
        d.line((x + CW - 32, y + 24, x + CW - 27, y + 29, x + CW - 19, y + 19), fill="white", width=3)
    d.text((x + 16, y + 44), title, font=F(600, 16), fill=(15, 23, 42))
    # bottom row
    d.rounded_rectangle((x + 16, y + 80, x + 28, y + 92), 2, outline=(148, 163, 184), width=2)
    d.text((x + 34, y + 78), due, font=F(500, 13), fill=(100, 116, 139))
    if st:
        a, b = st
        bx = x + 110
        d.rounded_rectangle((bx, y + 83, bx + 110, y + 89), 3, fill=(226, 232, 240))
        if a: d.rounded_rectangle((bx, y + 83, bx + int(110 * a / b), y + 89), 3, fill=(22, 163, 74) if a == b else INDIGO)
        d.text((bx + 118, y + 78), f"{a}/{b}", font=F(500, 13), fill=(100, 116, 139))
    c = AV[who]
    d.ellipse((x + CW - 44, y + 72, x + CW - 16, y + 100), fill=c)
    d.text((x + CW - 30, y + 86), who, font=F(700, 11), fill="white", anchor="mm")

def base(clock):
    im = Image.new("RGB", (W, H), (248, 250, 252)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 232, H), fill=(15, 23, 42))
    d.rounded_rectangle((24, 20, 54, 50), 8, fill=INDIGO)
    d.line((32, 35, 38, 41, 47, 29), fill="white", width=3)
    d.text((64, 23), "Taskflow", font=F(700, 20), fill="white")
    return im, d

def sidebar(d, active):
    for i, n in enumerate(["Board", "Calendar", "Reports", "Team", "Settings"]):
        y = 96 + i * 46
        if n == active: d.rounded_rectangle((14, y - 8, 218, y + 30), 8, fill=(30, 41, 59))
        d.rounded_rectangle((30, y + 3, 44, y + 17), 3, outline=(148, 163, 184), width=2)
        d.text((58, y), n, font=F(500, 15), fill="white" if n == active else (148, 163, 184))

def topbar(d, clock):
    d.rectangle((232, 0, W, 64), fill="white"); d.line((232, 64, W, 64), fill=(229, 231, 235))
    d.rounded_rectangle((256, 14, 640, 50), 10, fill=(243, 244, 246))
    d.ellipse((270, 24, 284, 38), outline=(156, 163, 175), width=2)
    d.text((294, 22), "Search tasks…", font=F(400, 15), fill=(156, 163, 175))
    d.text((1196, 22), clock, font=F(500, 15), fill=(107, 114, 128))
    d.ellipse((1300, 18, 1328, 46), outline=(156, 163, 175), width=2)
    d.ellipse((1374, 16, 1406, 48), fill=AV["AR"])
    d.text((1390, 32), "AR", font=F(700, 12), fill="white", anchor="mm")

_bc = {}
def board(cols, clock="10:24 AM", hidden=None, hl=None, subs=None, done=(), filt=False, page="board", fbtn=False):
    key = (tuple(tuple(c) for c in cols), clock, hidden, hl and round(hl[1], 2), filt, page, fbtn,
           tuple(sorted((subs or {}).items())), tuple(done))
    if key in _bc: return _bc[key]
    im, d = base(clock); sidebar(d, "Reports" if page == "reports" else "Board"); topbar(d, clock)
    if page == "reports":
        d.text((264, 92), "Reports", font=F(700, 26), fill=(15, 23, 42))
        d.text((264, 130), "Team velocity · last 6 weeks", font=F(400, 15), fill=(107, 114, 128))
        d.rounded_rectangle((264, 180, 1408, 620), 14, fill="white", outline=(226, 232, 240))
        for i, v in enumerate([180, 240, 210, 300, 280, 340]):
            x = 340 + i * 170
            d.rounded_rectangle((x, 580 - v, x + 80, 580), 8, fill=INDIGO)
            d.text((x + 40, 596), f"W{i + 1}", font=F(500, 13), fill=(100, 116, 139), anchor="mm")
    else:
        d.text((264, 92), "Q4 Launch", font=F(700, 26), fill=(15, 23, 42))
        d.text((264, 130), "Product team · 8 tasks", font=F(400, 15), fill=(107, 114, 128))
        d.rounded_rectangle((1104, 92, 1210, 132), 10, fill=(238, 242, 255) if fbtn else "white", outline=(203, 213, 225))
        for k in range(3):
            d.line((1124 + k * 2, 104 + k * 6, 1140 - k * 2, 104 + k * 6), fill=(71, 85, 105), width=2)
        d.text((1150, 102), "Filter", font=F(600, 15), fill=(51, 65, 85))
        d.rounded_rectangle((1224, 92, 1408, 132), 10, fill=INDIGO)
        d.text((1316, 112), "+  New task", font=F(600, 15), fill="white", anchor="mm")
        if filt:
            d.rounded_rectangle((264, 156, 432, 186), 15, fill=(238, 242, 255), outline=(165, 180, 252))
            d.text((280, 162), "Assigned to me   ×", font=F(600, 13), fill=INDIGO)
        for ci in range(3):
            y0 = COLY + (40 if filt else 0)
            d.rounded_rectangle((COLX[ci], y0, COLX[ci] + COLW, 880), 14, fill=(238, 242, 247))
            items = [c for c in cols[ci] if not filt or CARDS[c][3] == "AR"]
            d.text((COLX[ci] + 18, y0 + 16), COLNAMES[ci], font=F(700, 15), fill=(51, 65, 85))
            tw = d.textlength(COLNAMES[ci], font=F(700, 15))
            d.rounded_rectangle((COLX[ci] + 28 + tw, y0 + 15, COLX[ci] + 54 + tw, y0 + 35), 10, fill=(226, 232, 240))
            d.text((COLX[ci] + 41 + tw, y0 + 25), str(len(items)), font=F(600, 12), fill=(71, 85, 105), anchor="mm")
            for i, cid in enumerate(items):
                x, y = card_pos(ci, i, filt)
                if cid == hidden:
                    d.rounded_rectangle((x, y, x + CW, y + CH), 12, outline=(165, 180, 252), width=2, fill=(238, 242, 255))
                    continue
                draw_card(d, x, y, cid, (subs or {}).get(cid), cid in done, hl[1] if hl and hl[0] == cid else 0)
    _bc[key] = im
    return im

def ease(u): u = max(0, min(1, u)); return u * u * (3 - 2 * u)

def cursor(im, x, y, pressed=False, ripple=None):
    d = ImageDraw.Draw(im, "RGBA")
    if ripple is not None:
        r = 8 + 22 * ripple
        d.ellipse((x - r, y - r, x + r, y + r), outline=(79, 70, 229, int(200 * (1 - ripple))), width=3)
    s = 0.9 if pressed else 1.0
    pts = [(0, 0), (0, 22), (6, 17), (10, 27), (14, 25), (10, 16), (17, 16)]
    pts = [(x + px * s, y + py * s) for px, py in pts]
    d.polygon(pts, fill=(17, 24, 39), outline="white")
    d.line(pts + [pts[0]], fill="white", width=2)

class Path:
    def __init__(self, p0): self.keys = [(0, p0)]; self.moves = []
    def move(self, t0, t1, p1):
        self.moves.append((t0, t1, self.pos(t0), p1))
    def pos(self, t):
        p = self.keys[0][1]
        for t0, t1, a, b in self.moves:
            if t >= t1: p = b
            elif t >= t0:
                u = ease((t - t0) / (t1 - t0))
                return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        return p

def wiggle(path, t0, t1, c, amp=10):
    n = 4; dt = (t1 - t0) / n
    for i in range(n):
        path.move(t0 + i * dt, t0 + (i + 1) * dt, (c[0] + (amp if i % 2 == 0 else -amp), c[1] + (6 if i % 2 else -4)))
    path.move(t1, t1 + 0.2, c)

def ripple_at(clicks, t):
    for c in clicks:
        if 0 <= t - c < 0.4: return (t - c) / 0.4, t - c < 0.12
    return None, False

def overlay(im, alpha):
    o = Image.new("RGBA", im.size, (15, 23, 42, int(115 * alpha)))
    return Image.alpha_composite(im.convert("RGBA"), o).convert("RGB")

MX0, MY0, MX1, MY1 = 420, 170, 1020, 730
def modal(im, title_txt, prio, date, cal, a=1.0, caret=False):
    im = overlay(im, a)
    if a < 1:
        return im
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((MX0 + 4, MY0 + 8, MX1 + 4, MY1 + 8), 18, fill=(30, 35, 60))
    d.rounded_rectangle((MX0, MY0, MX1, MY1), 18, fill="white")
    d.text((MX0 + 32, MY0 + 28), "New task", font=F(700, 22), fill=(15, 23, 42))
    d.text((MX1 - 40, MY0 + 30), "×", font=F(500, 24), fill=(148, 163, 184))
    def field(y, label, val, ph=False, focus=False):
        d.text((MX0 + 32, y), label, font=F(600, 13), fill=(71, 85, 105))
        d.rounded_rectangle((MX0 + 32, y + 22, MX1 - 32, y + 66), 10, fill="white",
                            outline=INDIGO if focus else (203, 213, 225), width=2 if focus else 1)
        d.text((MX0 + 48, y + 34), val, font=F(400, 16), fill=(156, 163, 175) if ph else (15, 23, 42))
        return d.textlength(val, font=F(400, 16))
    tw = field(MY0 + 84, "Title", title_txt or "e.g. Prepare launch checklist", not title_txt, caret)
    if caret: d.line((MX0 + 50 + (tw if title_txt else 0), MY0 + 116, MX0 + 50 + (tw if title_txt else 0), MY0 + 136), fill=INDIGO, width=2)
    field(MY0 + 168, "Assignee", "        Alex Rivera")
    d.ellipse((MX0 + 46, MY0 + 199, MX0 + 68, MY0 + 221), fill=AV["AR"])
    d.text((MX0 + 32, MY0 + 252), "Priority", font=F(600, 13), fill=(71, 85, 105))
    for i, p in enumerate(["Low", "Medium", "High"]):
        x = MX0 + 32 + i * 120
        sel = p == prio
        col = {"Low": (22, 163, 74), "Medium": (202, 138, 4), "High": (220, 38, 38)}[p]
        d.rounded_rectangle((x, MY0 + 276, x + 108, MY0 + 314), 19, fill=col if sel else "white", outline=col, width=2)
        d.text((x + 54, MY0 + 295), p, font=F(600, 14), fill="white" if sel else col, anchor="mm")
    field(MY0 + 340, "Due date", date or "Select date", not date, cal)
    d.rounded_rectangle((MX1 - 330, MY1 - 70, MX1 - 200, MY1 - 26), 10, fill="white", outline=(203, 213, 225))
    d.text((MX1 - 265, MY1 - 48), "Cancel", font=F(600, 15), fill=(51, 65, 85), anchor="mm")
    d.rounded_rectangle((MX1 - 184, MY1 - 70, MX1 - 32, MY1 - 26), 10, fill=INDIGO)
    d.text((MX1 - 108, MY1 - 48), "Create task", font=F(600, 15), fill="white", anchor="mm")
    if cal:
        cx, cy = MX0 + 32, MY0 + 412
        d.rounded_rectangle((cx + 3, cy + 5, cx + 303, cy + 205), 12, fill=(203, 213, 225))
        d.rounded_rectangle((cx, cy, cx + 300, cy + 200), 12, fill="white", outline=(203, 213, 225))
        d.text((cx + 16, cy + 12), "November 2026", font=F(700, 14), fill=(15, 23, 42))
        for i in range(30):
            r, c = divmod(i, 7)
            x, y = cx + 20 + c * 39, cy + 44 + r * 30
            if i + 1 == 20:
                d.ellipse((x - 4, y - 4, x + 26, y + 22), fill=INDIGO)
            d.text((x + 11, y + 9), str(i + 1), font=F(500, 13), fill="white" if i + 1 == 20 else (51, 65, 85), anchor="mm")
    return im

def day20_pos():
    cx, cy = MX0 + 32, MY0 + 412
    r, c = divmod(19, 7)
    return cx + 20 + c * 39 + 11, cy + 44 + r * 30 + 9

def toast(im, text, color, a):
    if a <= 0: return im
    o = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    w = d.textlength(text, font=F(600, 15)) + 64
    x1 = 1416; x0 = x1 - w; y0 = 84 - int((1 - a) * 12)
    d.rounded_rectangle((x0, y0, x1, y0 + 52), 12, fill=color + (int(255 * a),))
    d.ellipse((x0 + 16, y0 + 16, x0 + 36, y0 + 36), outline=(255, 255, 255, int(255 * a)), width=2)
    d.text((x0 + 46, y0 + 16), text, font=F(600, 15), fill=(255, 255, 255, int(255 * a)))
    return Image.alpha_composite(im.convert("RGBA"), o).convert("RGB")

def spinner(im, t):
    o = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    d.rectangle((232, 65, W, H), fill=(248, 250, 252, 190))
    cx, cy, r = 836, 500, 26
    a0 = (t * 360 * 1.3) % 360
    d.arc((cx - r, cy - r, cx + r, cy + r), 0, 360, fill=(226, 232, 240, 255), width=6)
    d.arc((cx - r, cy - r, cx + r, cy + r), a0, a0 + 100, fill=INDIGO + (255,), width=6)
    d.text((cx, cy + 50), "Loading…", font=F(500, 15), fill=(100, 116, 139, 255), anchor="mm")
    return Image.alpha_composite(im.convert("RGBA"), o).convert("RGB")

def drag_card(im, x, y, cid, sub=None):
    o = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    d.rounded_rectangle((x + 6, y + 10, x + CW + 6, y + CH + 10), 12, fill=(15, 23, 42, 50))
    im = Image.alpha_composite(im.convert("RGBA"), o).convert("RGB")
    draw_card(ImageDraw.Draw(im), int(x), int(y), cid, sub, hl=1.0)
    return im

def dropdown(im):
    d = ImageDraw.Draw(im)
    x0, y0 = 1104, 140
    d.rounded_rectangle((x0 - 80 + 3, y0 + 4, x0 + 106 + 3, y0 + 152 + 4), 12, fill=(203, 213, 225))
    d.rounded_rectangle((x0 - 80, y0, x0 + 106, y0 + 152), 12, fill="white", outline=(203, 213, 225))
    for i, n in enumerate(["Assigned to me", "High priority", "Due this week"]):
        d.text((x0 - 62, y0 + 18 + i * 44), n, font=F(500, 15), fill=(30, 41, 59))
    return im

def encoder(path):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                             "-crf", "16", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)

COLS0 = [["notes", "pricing", "qa"], ["onb", "api"], ["kick", "research"]]
BTN_NEW = (1316, 112); BTN_FILTER = (1156, 112)
TITLE_F = (MX0 + 200, MY0 + 128); HIGH = (MX0 + 32 + 240 + 54, MY0 + 295)
DATE_F = (MX0 + 200, MY0 + 384); CREATE = (MX1 - 108, MY1 - 48)
TYPED = "Prepare client demo"

def part1(out):
    T = 33.0
    p = Path((900, 520))
    p.move(3.0, 5.2, BTN_NEW)
    p.move(9.2, 10.0, TITLE_F)
    p.move(13.0, 13.9, HIGH)
    p.move(14.4, 15.3, DATE_F)
    p.move(15.7, 16.5, day20_pos())
    p.move(17.0, 17.9, CREATE)
    wiggle(p, 21.0, 21.7, CREATE, 8)
    p.move(21.9, 22.0, CREATE)
    cx, cy = card_pos(0, 0)
    grab = (cx + 170, cy + 50)
    p.move(26.4, 27.8, grab)
    dx, dy = card_pos(1, 0)
    p.move(28.2, 30.0, (dx + 170, dy + 50))
    p.move(30.6, 31.6, (dx + 260, dy + 260))
    clicks = [5.4, 10.1, 14.1, 15.4, 16.6, 18.0, 22.0, 28.0, 30.1]
    enc = encoder(out)
    for f in range(int(T * FPS)):
        t = f / FPS
        x, y = p.pos(t)
        if t < 22.2:
            im = board(COLS0)
        else:
            cols = [["demo"] + COLS0[0], COLS0[1], COLS0[2]]
            hl = ("demo", max(0, 1 - (t - 22.6) / 2.0)) if t < 28.0 else None
            if 28.0 <= t < 30.1:
                im = board(cols, hidden="demo")
                # placeholder moves to in-progress column when hovering it
                if t > 29.2:
                    im = board([COLS0[0], ["demo"] + COLS0[1], COLS0[2]], hidden="demo")
            elif t >= 30.1:
                im = board([COLS0[0], ["demo"] + COLS0[1], COLS0[2]])
            else:
                im = board(cols, hl=hl)
        im = im.copy()
        if 5.6 <= t < 8.6:
            im = spinner(im, t)
        if 8.6 <= t < 22.2:
            a = min(1, (t - 8.6) / 0.2)
            title = TYPED[:max(0, min(len(TYPED), int((t - 10.3) / 2.5 * len(TYPED))))] if t > 10.3 else ""
            prio = "High" if t >= 14.1 else "Medium"
            date = "Nov 20, 2026" if t >= 16.6 else ""
            cal = 15.4 <= t < 16.6
            im = modal(im, title, prio, date, cal, a, caret=(10.1 <= t < 13.0))
        if 18.1 <= t < 21.0:
            a = min(1, (t - 18.1) / 0.25, (20.8 - t) / 0.25) if t < 20.8 else 0
            im = toast(im, "Something went wrong. Please try again.", (220, 38, 38), a)
        if 22.3 <= t < 25.3:
            a = min(1, (t - 22.3) / 0.25, (25.3 - t) / 0.3)
            im = toast(im, "Task created", (22, 163, 74), a)
        if 28.0 <= t < 30.1:
            im = drag_card(im, x - 170, y - 50, "demo")
        rp, pr = ripple_at(clicks, t)
        cursor(im, x, y, pr, rp)
        enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()
    return im

def part2(out):
    T = 23.0
    cols = [COLS0[0], ["demo"] + COLS0[1], COLS0[2]]
    dx, dy = card_pos(1, 0)
    p = Path((dx + 260, dy + 260))
    p.move(1.4, 2.7, (dx + 170, dy + 50))
    ex, ey = card_pos(2, 0)
    p.move(3.0, 4.8, (ex + 170, ey + 50))
    p.move(5.2, 6.4, (ex + 200, ey + 330))
    p.move(7.0, 7.7, (110, 196 + 10))            # detour to Reports
    p.move(10.2, 10.9, (110, 96 + 10))           # back to Board
    p.move(11.4, 12.5, BTN_FILTER)
    p.move(13.0, 13.8, (1080, 167))
    p.move(14.6, 16.0, (card_pos(1, 0, True)[0] + 200, card_pos(1, 0, True)[1] + 60))
    p.move(17.0, 18.4, (card_pos(2, 0, True)[0] + 160, card_pos(2, 0, True)[1] + 60))
    p.move(19.4, 20.8, (card_pos(0, 1, True)[0] + 180, card_pos(0, 1, True)[1] + 60))
    clicks = [2.9, 4.9, 7.8, 11.0, 12.6, 13.9]
    sub = {"demo": (3, 3)}
    enc = encoder(out)
    for f in range(int(T * FPS)):
        t = f / FPS
        x, y = p.pos(t)
        clock = "10:31 AM"
        if t < 2.9:
            im = board(cols, clock, subs=sub)
        elif t < 4.9:
            c2 = cols if t < 4.0 else [COLS0[0], COLS0[1], ["demo"] + COLS0[2]]
            im = board(c2, clock, hidden="demo", subs=sub)
        else:
            done_cols = [COLS0[0], COLS0[1], ["demo"] + COLS0[2]]
            if 7.9 <= t < 11.1:
                im = board(done_cols, clock, page="reports")
            elif t >= 13.9:
                im = board(done_cols, clock, subs=sub, done=("demo",), filt=True, fbtn=True)
            else:
                im = board(done_cols, clock, subs=sub, done=("demo",), fbtn=t >= 12.6)
        im = im.copy()
        if 12.6 <= t < 13.9:
            im = dropdown(im)
        if 2.9 <= t < 4.9:
            im = drag_card(im, x - 170, y - 50, "demo", (3, 3))
        rp, pr = ripple_at(clicks, t)
        cursor(im, x, y, pr, rp)
        enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    last = part1("build/p1.mp4")
    last.save("build/idle.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-i", "build/idle.png",
                    "-t", "150", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-tune", "stillimage", "build/idle.mp4"], check=True)
    part2("build/p2.mp4")
    with open("build/list.txt", "w") as fh:
        fh.write("file 'p1.mp4'\nfile 'idle.mp4'\nfile 'p2.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-i", "build/list.txt", "-c", "copy",
                    "build/recording.mp4"], check=True)
    print("ok")
