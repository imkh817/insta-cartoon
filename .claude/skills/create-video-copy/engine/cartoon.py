"""create-video-copy 그리기 엔진.

손그림(boil) 펜, 캐릭터(토끼 여친 / 곰 남친), 소품, 2x2 4컷 레이아웃 렌더러.
에피소드 파일은 `from cartoon import *` 로 이 모듈을 가져다 쓴다.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
SS = 2
FPS = 10
N = 96            # 9.6초 루프 (boil 3 / 포즈 6·12·24 주기로 딱 나눠떨어짐)

FONT = "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"

INK = (30, 24, 24)
WHITE = (255, 255, 255)
BUNNY = (255, 205, 218)
BUNNY_IN = (255, 150, 180)
RIBBON = (255, 70, 150)
BEAR = (176, 112, 64)
MUZZLE = (247, 226, 196)
BLUSH = (255, 120, 150)
YELLOW = (255, 238, 80)
SPARK = (255, 205, 40)
TEAR = (140, 205, 255)
HOODIE = (140, 140, 155)
RED = (220, 50, 60)
TONGUE = (255, 120, 140)
MOUTH = (150, 30, 45)

_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, int(size * SS))
    return _fonts[size]


def rot(cx, cy, dx, dy, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (cx + dx * c - dy * s, cy + dx * s + dy * c)


class Pen:
    def __init__(self, img, boil):
        self.d = ImageDraw.Draw(img)
        self.boil = boil
        self.ph = [boil * 2.3 + k * 1.7 for k in range(4)]
        self.amp = 2.4
        self.ox = self.oy = 0
        self.k = 1.0      # 컷 좌표 확대 배율 (슬라이드형에서 사용)
        self.kw = 1.0     # 선 굵기 배율
        self.seed = 0

    # 손떨림 변위장 (boil마다 위상이 바뀜)
    def j(self, x, y):
        x = x * self.k + self.ox
        y = y * self.k + self.oy
        a, p = self.amp, self.ph
        dx = a * (math.sin(0.05 * y + 0.03 * x + p[0]) * 0.7 + math.sin(0.09 * y - 0.06 * x + p[1]) * 0.3)
        dy = a * (math.sin(0.045 * x - 0.03 * y + p[2]) * 0.7 + math.sin(0.08 * x + 0.07 * y + p[3]) * 0.3)
        return ((x + dx) * SS, (y + dy) * SS)

    # 굵기가 들쭉날쭉한 펜 선 (원 도장 찍기)
    def stroke(self, pts, w=7, closed=False, color=INK):
        P = [self.j(x, y) for x, y in pts]
        if closed:
            P = P + [P[0]]
        segs = list(zip(P, P[1:]))
        L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs) or 1
        step = 1.3 * SS
        self.seed += 1.7
        sd = self.seed + self.boil * 0.9
        s = 0.0
        base = w * self.kw * SS / 2
        for (x0, y0), (x1, y1) in segs:
            l = math.hypot(x1 - x0, y1 - y0)
            n = max(1, int(l / step))
            for i in range(n):
                f = i / n
                x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                ss = s + l * f
                r = base * (0.8 + 0.2 * math.sin(ss * 0.018 + sd) + 0.1 * math.sin(ss * 0.07 + 2 * sd))
                if not closed:
                    tp = min(1.0, ss / (8 * SS), (L - ss) / (8 * SS))
                    r *= 0.5 + 0.5 * max(0.0, tp)
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=color)
            s += l

    def shape(self, pts, fill=None, w=7, color=INK):
        if fill is not None:
            self.d.polygon([self.j(x, y) for x, y in pts], fill=fill)
        if w:
            self.stroke(pts, w, True, color)

    def blob(self, cx, cy, rx, ry, fill=None, w=7, ang=0, irr=0.025, k=0.0, color=INK):
        n = max(24, int((rx + ry) / 2.5))
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            f = 1 + irr * math.sin(3 * a + k) + irr * 0.6 * math.sin(5 * a + 2 * k)
            pts.append(rot(cx, cy, rx * f * math.cos(a), ry * f * math.sin(a), ang))
        self.shape(pts, fill, w, color)

    def capsule(self, p0, p1, r0, r1=None, fill=WHITE, w=7):
        r1 = r0 if r1 is None else r1
        (x0, y0), (x1, y1) = p0, p1
        th = math.atan2(y1 - y0, x1 - x0)
        pts = []
        for i in range(13):
            a = th - math.pi / 2 + math.pi * i / 12
            pts.append((x1 + r1 * math.cos(a), y1 + r1 * math.sin(a)))
        for i in range(13):
            a = th + math.pi / 2 + math.pi * i / 12
            pts.append((x0 + r0 * math.cos(a), y0 + r0 * math.sin(a)))
        self.shape(pts, fill, w)

    def arc(self, cx, cy, rx, ry, a0, a1, w=5, ang=0, color=INK):
        n = max(8, int(abs(a1 - a0) / 8))
        pts = [rot(cx, cy, rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                   ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)), ang) for i in range(n + 1)]
        self.stroke(pts, w, False, color)

    def line(self, pts, w=6, color=INK):
        out = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 14))
            out += [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n)]
        out.append(pts[-1])
        self.stroke(out, w, False, color)

    def text(self, x, y, s, size, fill=INK, anchor="mm", wobble=False):
        X, Y = self.j(x, y) if wobble else ((x * self.k + self.ox) * SS, (y * self.k + self.oy) * SS)
        self.d.text((X, Y), s, font=font(size * self.k), fill=fill, anchor=anchor)

    def text_w(self, s, size):
        b = font(size * self.k).getbbox(s)
        return (b[2] - b[0]) / SS / self.k

    def heart(self, cx, cy, s, fill=RIBBON, w=5):
        pts = []
        for i in range(32):
            t = 2 * math.pi * i / 32
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            pts.append((cx + x * s / 16, cy + y * s / 16))
        self.shape(pts, fill, w)

    def sparkle(self, cx, cy, s, fill=SPARK, w=4):
        pts = []
        for i in range(36):
            a = 2 * math.pi * i / 36
            c, si = math.cos(a), math.sin(a)
            pts.append((cx + s * c * abs(c) ** 2, cy + s * si * abs(si) ** 2))
        self.shape(pts, fill, w)

    def bubble(self, x, y, s, size, tail):
        tw = self.text_w(s, size)
        rx, ry = tw / 2 + 26, size * 0.5 + 20
        tx, ty = tail
        bx = max(-rx * 0.4, min(rx * 0.4, (tx - x) * 0.5))
        by = ry * 0.6 if ty > y else -ry * 0.6
        self.shape([(x + bx - 13, y + by), (tx, ty), (x + bx + 13, y + by)], WHITE, 6)
        self.blob(x, y, rx, ry, WHITE, 6, irr=0.03, k=len(s))
        self.text(x, y + 2, s, size)


# ---------------- 캐릭터 ----------------

def face(p, hx, hy, hr, tilt, eyes, mouth, extras=(), muzzle=False):
    def H(dx, dy):
        return rot(hx, hy, dx * hr, dy * hr, tilt)

    ex = 0.36
    for sgn in (-1, 1):
        cx, cy = H(sgn * ex, 0.02)
        if eyes in ("sparkle", "teary"):
            p.blob(cx, cy, 0.2 * hr, 0.24 * hr, WHITE, 5, ang=tilt)
            px, py = H(sgn * ex + 0.02, 0.06)
            p.blob(px, py, 0.15 * hr, 0.18 * hr, INK, 0, ang=tilt)
            hx1, hy1 = H(sgn * ex - 0.05, -0.04)
            p.blob(hx1, hy1, 0.06 * hr, 0.07 * hr, WHITE, 0)
            hx2, hy2 = H(sgn * ex + 0.07, 0.13)
            p.blob(hx2, hy2, 0.03 * hr, 0.03 * hr, WHITE, 0)
            # 속눈썹
            for k in (-1, 0, 1):
                a0 = H(sgn * (ex + 0.13 + 0.03 * k), -0.18 + 0.05 * k)
                a1 = H(sgn * (ex + 0.24 + 0.03 * k), -0.27 + 0.07 * k)
                p.line([a0, a1], 4)
            if eyes == "teary":
                tx, ty = H(sgn * (ex + 0.02), 0.3)
                p.blob(tx, ty, 0.07 * hr, 0.1 * hr, TEAR, 4)
                p.arc(*H(sgn * ex, -0.38), 0.14 * hr, 0.05 * hr, 200, 340, 5, ang=tilt + sgn * 15)
        elif eyes == "heart":
            p.heart(cx, cy, 0.17 * hr, (255, 60, 110), 4)
        elif eyes == "dot":
            p.blob(cx, cy, 0.06 * hr, 0.075 * hr, INK, 0)
        elif eyes == "down":
            p.blob(*H(sgn * ex, 0.1), 0.06 * hr, 0.06 * hr, INK, 0)
        elif eyes == "happy":
            p.arc(cx, cy + 0.05 * hr, 0.13 * hr, 0.11 * hr, 200, 340, 5, ang=tilt)
        elif eyes == "closed":
            p.arc(cx, cy - 0.04 * hr, 0.13 * hr, 0.08 * hr, 15, 165, 5, ang=tilt)
        elif eyes == "squeeze":      # 질끈 감은 눈 > <
            p.line([H(sgn * (ex + 0.13), -0.1), H(sgn * (ex - 0.1), 0.02), H(sgn * (ex + 0.13), 0.13)], 5)
        elif eyes == "half":
            p.line([H(sgn * ex - 0.15, -0.01), H(sgn * ex + 0.15, -0.01)], 5)
            p.arc(*H(sgn * ex, -0.01), 0.1 * hr, 0.09 * hr, 10, 170, 5, ang=tilt)
            p.arc(*H(sgn * ex, 0.15), 0.13 * hr, 0.05 * hr, 20, 160, 3, ang=tilt, color=(150, 140, 170))
    if muzzle:
        mx, my = H(0, 0.42)
        p.blob(mx, my, 0.4 * hr, 0.3 * hr, MUZZLE, 5, ang=tilt)
        nx, ny = H(0, 0.3)
        p.blob(nx, ny, 0.1 * hr, 0.07 * hr, INK, 0)
    if "blush" in extras or "blush+" in extras:
        for sgn in (-1, 1):
            bx, by = H(sgn * 0.62, 0.3)
            p.blob(bx, by, 0.15 * hr, 0.09 * hr, BLUSH, 0, ang=tilt)
            if "blush+" in extras:
                for k in range(3):
                    p.line([H(sgn * 0.62 + (k - 1) * 0.08 - 0.03, 0.36), H(sgn * 0.62 + (k - 1) * 0.08 + 0.03, 0.24)], 3)
    my0 = 0.5 if not muzzle else 0.56
    mx, my = H(0, my0)
    if mouth == "kiss":
        p.heart(mx, my, 0.12 * hr, RED, 4)
    elif mouth == "smile":
        p.arc(mx, my - 0.06 * hr, 0.12 * hr, 0.09 * hr, 20, 160, 5, ang=tilt)
    elif mouth == "grin":
        pts = [H(-0.17, my0 - 0.04), H(0.17, my0 - 0.04)] + [
            H(0.17 * math.cos(math.radians(a)), my0 - 0.04 + 0.16 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
        p.shape(pts, MOUTH, 5)
    elif mouth == "flat":
        p.line([H(-0.1, my0), H(0.1, my0)], 5)
    elif mouth == "wobbly":
        p.line([H(-0.16 + 0.08 * i, my0 + (0.04 if i % 2 else -0.03)) for i in range(5)], 5)
    elif mouth == "yawn":
        p.blob(mx, my + 0.08 * hr, 0.17 * hr, 0.23 * hr, MOUTH, 5, ang=tilt)
        p.blob(*H(0, my0 + 0.22), 0.1 * hr, 0.06 * hr, TONGUE, 0)
    elif mouth == "o":
        p.blob(mx, my, 0.08 * hr, 0.1 * hr, MOUTH, 5)
    elif mouth == "drool":
        p.blob(mx, my, 0.07 * hr, 0.06 * hr, MOUTH, 4)
        dx, dy = H(0.06, my0 + 0.05)
        p.capsule((dx, dy), (dx + 2, dy + 0.3 * hr), 3, 7, TEAR, 4)
    if "boogers" in extras:
        for sgn in (-1, 1):
            p.blob(*H(sgn * (ex - 0.2), 0.06), 0.035 * hr, 0.035 * hr, (240, 200, 60), 3)
    if "sweat" in extras:
        sx, sy = H(0.75, -0.35)
        p.shape([(sx, sy - 18), (sx + 10, sy + 4), (sx, sy + 12), (sx - 10, sy + 4)], TEAR, 4)


def bunny(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None,
          arms=(), arms_back=(), ribbon=True, ears="up", body_fill=BUNNY, legs=(), face_fill=BUNNY):
    for (sx, sy), (ax, ay) in arms_back:
        p.capsule((sx, sy), (ax, ay), 17, 20, body_fill)
    if body:
        bx, by, brx, bry = body
        for (lx, ly), (fx, fy) in legs:
            p.capsule((lx, ly), (fx, fy), 18, 21, BUNNY)
        p.blob(bx, by, brx, bry, body_fill, 7)
        if body_fill == HOODIE:
            p.line([(bx, by - bry * 0.8), (bx, by + bry * 0.7)], 4, (230, 230, 235))
    # 귀
    ear_set = [(-0.38, -10), (0.38, 10)]
    for i, (dx, da) in enumerate(ear_set):
        bx, by = rot(hx, hy, dx * hr, -0.85 * hr, tilt)
        ang = tilt + da
        if ears == "messy" and i == 1:
            ang = tilt + 75
        elif ears == "messy":
            ang = tilt - 25
        cx, cy = rot(bx, by, 0, -0.55 * hr, ang)
        p.blob(cx, cy, 0.24 * hr, 0.62 * hr, BUNNY, 7, ang=ang, k=i)
        p.blob(*rot(bx, by, 0, -0.5 * hr, ang), 0.11 * hr, 0.42 * hr, BUNNY_IN, 0, ang=ang)
    p.blob(hx, hy, 1.08 * hr, 0.95 * hr, face_fill, 8, ang=tilt, k=1.3)
    if ribbon:
        rx_, ry_ = rot(hx, hy, 0.05 * hr, -0.86 * hr, tilt)
        for sgn in (-1, 1):
            c = rot(rx_, ry_, sgn * 0.26 * hr, 0, tilt)
            pts = [rot(rx_, ry_, 0, 0, tilt), rot(rx_, ry_, sgn * 0.45 * hr, -0.22 * hr, tilt),
                   rot(rx_, ry_, sgn * 0.5 * hr, 0.02 * hr, tilt), rot(rx_, ry_, sgn * 0.42 * hr, 0.22 * hr, tilt)]
            p.shape(pts, RIBBON, 6)
        p.blob(rx_, ry_, 0.12 * hr, 0.11 * hr, RIBBON, 6)
    if ears == "messy":
        for k in range(3):
            a0 = rot(hx, hy, (-0.2 + 0.18 * k) * hr, -0.93 * hr, tilt)
            a1 = rot(hx, hy, (-0.25 + 0.2 * k) * hr, -1.15 * hr, tilt)
            p.line([a0, a1], 4)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    for (sx, sy), (ax, ay) in arms:
        p.capsule((sx, sy), (ax, ay), 17, 20, body_fill)


def bear(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), arms_back=(),
         face_fill=BEAR):
    for (sx, sy), (ax, ay) in arms_back:
        p.capsule((sx, sy), (ax, ay), 18, 22, BEAR)
    if body:
        bx, by, brx, bry = body
        p.blob(bx, by, brx, bry, BEAR, 7)
        p.blob(bx, by + bry * 0.1, brx * 0.6, bry * 0.6, MUZZLE, 0)
    for sgn in (-1, 1):
        ex_, ey_ = rot(hx, hy, sgn * 0.72 * hr, -0.68 * hr, tilt)
        p.blob(ex_, ey_, 0.3 * hr, 0.3 * hr, BEAR, 7)
        p.blob(ex_, ey_, 0.15 * hr, 0.15 * hr, MUZZLE, 0)
    p.blob(hx, hy, 1.08 * hr, 0.95 * hr, face_fill, 8, ang=tilt, k=2.1)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras, muzzle=True)
    for (sx, sy), (ax, ay) in arms:
        p.capsule((sx, sy), (ax, ay), 18, 22, BEAR)


def popcorn(p, x, y, s=1.0, tipped=False):
    ang = 70 if tipped else 0
    pts = [rot(x, y, dx * s, dy * s, ang) for dx, dy in ((-34, -40), (34, -40), (26, 40), (-26, 40))]
    p.shape(pts, WHITE, 6)
    for k in (-1, 1):
        st = [rot(x, y, dx * s, dy * s, ang) for dx, dy in ((k * 16 - 7, -38), (k * 16 + 7, -38), (k * 12 + 6, 38), (k * 12 - 6, 38))]
        p.shape(st, RED, 0)
    p.shape(pts, None, 6)
    tops = ((-22, -48), (0, -54), (22, -48), (-10, -62), (12, -62))
    if tipped:
        tops = ((-70, 30), (-95, 45), (-60, 50))
        for dx, dy in tops:
            p.blob(x + dx * s, y + dy * s, 13 * s, 11 * s, (255, 246, 205), 5)
        return
    for dx, dy in tops:
        p.blob(*rot(x, y, dx * s, dy * s, ang), 14 * s, 12 * s, (255, 246, 205), 5)



# ---------------- 2x2 레이아웃 ----------------
CW, CH = 470, 450          # 컷 로컬 좌표 크기
X0 = [50, 560]
Y0 = [575, 1125]
DEFAULT_TAG_COLORS = {}


def render_frame(ep, t):
    img = Image.new("RGB", (W * SS, H * SS), WHITE)
    p = Pen(img, t % 3)

    # 제목 상자 (1~2줄)
    p.shape([(90, 300), (990, 296), (994, 470), (86, 474)], YELLOW, 7)
    lines = ep.TITLE if isinstance(ep.TITLE, (list, tuple)) else [ep.TITLE]
    ys = [386] if len(lines) == 1 else [352, 420]
    for y, s in zip(ys, lines):
        p.text(540, y, s, 54)

    tag_colors = getattr(ep, "TAG_COLORS", DEFAULT_TAG_COLORS)
    for i, (fn, tag, cap) in enumerate(ep.CELLS):
        x0, y0 = X0[i % 2], Y0[i // 2]
        p.ox, p.oy = x0, y0
        fn(p, t)
        p.ox = p.oy = 0
        tag_s = tag + " " if tag else ""
        tw = p.text_w(tag_s, 30) if tag_s else 0
        cw = p.text_w(cap, 30)
        cx = x0 + CW / 2 - (tw + cw) / 2
        if tag_s:
            p.text(cx, y0 + CH + 32, tag_s, 30, tag_colors.get(tag, INK), anchor="lm")
        p.text(cx + tw, y0 + CH + 32, cap, 30, anchor="lm")

    return img.resize((W, H), Image.LANCZOS)


# ---------------- 1x1 슬라이드 레이아웃 ----------------
SLIDE_K = 2.0              # 컷 확대 배율 (470x450 -> 940x900)
SLIDE_X0, SLIDE_Y0 = 70, 640
FADE = 3                   # 페이드 프레임 수 (나갈 때/들어올 때 각각)


def _slide_base(p, ep, idx, n_slides):
    p.shape([(90, 250), (990, 246), (994, 420), (86, 424)], YELLOW, 7)
    lines = ep.TITLE if isinstance(ep.TITLE, (list, tuple)) else [ep.TITLE]
    ys = [336] if len(lines) == 1 else [302, 370]
    for y, s in zip(ys, lines):
        p.text(540, y, s, 54)
    if not getattr(ep, "DOTS", False):   # 진행 점은 기본으로 표시하지 않음 (사용자 피드백)
        return
    gap = 44
    x = 540 - gap * (n_slides - 1) / 2
    for i in range(n_slides):
        on = i == idx
        p.blob(x + i * gap, 1620, 11 if on else 8, 11 if on else 8, RIBBON if on else (225, 220, 225), 4 if on else 0)


def render_frame_slide(ep, t):
    slides = ep.SLIDES
    per = ep.FRAMES_PER_SLIDE
    idx, local = divmod(t, per)
    idx %= len(slides)
    fn, tag, cap = slides[idx]
    tag_colors = getattr(ep, "TAG_COLORS", DEFAULT_TAG_COLORS)

    def draw(with_cut):
        img = Image.new("RGB", (W * SS, H * SS), WHITE)
        p = Pen(img, t % 3)
        _slide_base(p, ep, idx, len(slides))
        if with_cut:
            # 캡션 (컷 위)
            tag_s = tag + " " if tag else ""
            tw = p.text_w(tag_s, 46) if tag_s else 0
            cw = p.text_w(cap, 46)
            cx = 540 - (tw + cw) / 2
            if tag_s:
                p.text(cx, 540, tag_s, 46, tag_colors.get(tag, INK), anchor="lm")
            p.text(cx + tw, 540, cap, 46, anchor="lm")
            p.ox, p.oy, p.k, p.kw = SLIDE_X0, SLIDE_Y0, SLIDE_K, 1.45
            fn(p, t)
            p.ox = p.oy = 0
            p.k = p.kw = 1.0
        return img

    full = draw(True)
    a = 1.0
    if local < FADE:
        a = (local + 1) / (FADE + 1)
    elif local >= per - FADE:
        a = (per - local) / (FADE + 1)
    if a < 1.0:
        full = Image.blend(draw(False), full, a)
    return full.resize((W, H), Image.LANCZOS)


# ---------------- 추가 캐릭터 (캐릭터 시안) ----------------
CAT = (255, 186, 104)
CAT_D = (222, 128, 48)
DOG = (252, 247, 236)
DOG_EAR = (172, 112, 66)
HAM = (246, 192, 122)
HAM_W = (255, 251, 242)
PENG = (52, 62, 98)
BEAK = (255, 168, 44)
MOCHI = (255, 230, 239)
POTATO = (214, 168, 104)
POTATO_D = (166, 120, 66)
LEAF = (112, 190, 88)
INNER = (255, 160, 185)


def _H(hx, hy, hr, tilt):
    return lambda dx, dy: rot(hx, hy, dx * hr, dy * hr, tilt)


def bow(p, cx, cy, s, tilt=0, fill=RIBBON):
    """핫핑크 리본 (s = 리본 반폭)."""
    for sgn in (-1, 1):
        pts = [rot(cx, cy, 0, 0, tilt), rot(cx, cy, sgn * 0.9 * s, -0.45 * s, tilt),
               rot(cx, cy, sgn * 1.0 * s, 0.04 * s, tilt), rot(cx, cy, sgn * 0.84 * s, 0.45 * s, tilt)]
        p.shape(pts, fill, 6)
    p.blob(cx, cy, 0.24 * s, 0.22 * s, fill, 6)


def _limbs(p, arms, fill, r=17):
    for (sx, sy), (ax, ay) in arms:
        p.capsule((sx, sy), (ax, ay), r, r + 3, fill)


def cat(p, hx, hy, hr, tilt=0, eyes="dot", mouth="w", extras=(), body=None, arms=(),
        ribbon=True, face_fill=CAT, tail=True):
    """여친 후보: 치즈냥 (줄무늬 이마, 세모 귀, 수염, 꼬리)."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        if tail:
            p.capsule((bx + brx * 0.7, by + bry * 0.4), (bx + brx * 1.45, by - bry * 0.7), 12, 14, CAT)
            p.blob(bx + brx * 1.45, by - bry * 0.7, 12, 12, CAT_D, 0)
        p.blob(bx, by, brx, bry, CAT, 7)
        p.blob(bx, by + bry * 0.15, brx * 0.55, bry * 0.6, (255, 226, 186), 0)
    for sgn in (-1, 1):
        p.shape([H(sgn * 0.82, -0.45), H(sgn * 0.22, -0.88), H(sgn * 0.78, -1.32)], CAT, 7)
        p.shape([H(sgn * 0.68, -0.6), H(sgn * 0.38, -0.8), H(sgn * 0.7, -1.08)], INNER, 0)
    p.blob(hx, hy, 1.08 * hr, 0.95 * hr, face_fill, 8, ang=tilt, k=0.7)
    for dx in (-0.16, 0, 0.16):
        p.line([H(dx, -0.92), H(dx * 0.8, -0.66)], 6, CAT_D)
    if ribbon:
        bow(p, *H(0.62, -1.0), 0.32 * hr, tilt + 20)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    for sgn in (-1, 1):
        for dy in (-0.06, 0.1):
            p.line([H(sgn * 0.78, 0.3 + dy * 0.3), H(sgn * 1.28, 0.25 + dy)], 3)
    _limbs(p, arms, CAT)


def dog(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), face_fill=DOG):
    """남친 후보: 백구 (처진 갈색 귀, 눈 얼룩, 빨간 목줄)."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        p.blob(bx, by, brx, bry, DOG, 7)
        p.blob(bx + brx * 0.35, by + bry * 0.1, brx * 0.3, bry * 0.28, DOG_EAR, 0)
    p.blob(hx, hy, 1.08 * hr, 0.95 * hr, face_fill, 8, ang=tilt, k=1.1)
    p.blob(*H(0.38, -0.08), 0.27 * hr, 0.24 * hr, DOG_EAR, 0, ang=tilt)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras, muzzle=True)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.98, -0.12), 0.27 * hr, 0.58 * hr, DOG_EAR, 7, ang=tilt + sgn * 18, k=sgn)
    if body:
        p.capsule(H(-0.5, 0.9), H(0.5, 0.9), 8, 8, (230, 60, 70), 5)
        p.blob(*H(0, 1.02), 0.1 * hr, 0.1 * hr, SPARK, 4)
    _limbs(p, arms, DOG)


def hamster(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(),
            ribbon=True, cheeks=1.0, face_fill=HAM):
    """여친 후보: 햄찌 (빵빵한 볼주머니, 작은 귀). cheeks로 볼 크기 조절 (먹방 개그)."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        p.blob(bx, by, brx, bry, HAM, 7)
        p.blob(bx, by + bry * 0.15, brx * 0.65, bry * 0.65, HAM_W, 0)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.62, -0.84), 0.22 * hr, 0.2 * hr, HAM, 7)
        p.blob(*H(sgn * 0.62, -0.84), 0.11 * hr, 0.1 * hr, INNER, 0)
    p.blob(hx, hy, 1.15 * hr, 0.98 * hr, face_fill, 8, ang=tilt, k=0.4)
    p.blob(*H(0, 0.32), 0.8 * hr, 0.5 * hr, HAM_W, 0, ang=tilt)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.74, 0.34), 0.34 * hr * cheeks, 0.28 * hr * cheeks, HAM_W, 6, ang=tilt)
    if ribbon:
        bow(p, *H(0, -0.92), 0.36 * hr, tilt)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    _limbs(p, arms, HAM, 14)


def penguin(p, hx, hy, hr, tilt=0, eyes="dot", mouth="flat", extras=(), body=None, arms=()):
    """남친 후보: 펭구 (남색, 흰 얼굴, 주황 부리, 삐친 머리털)."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        p.blob(bx, by, brx, bry, PENG, 7)
        p.blob(bx, by + bry * 0.12, brx * 0.68, bry * 0.75, WHITE, 0)
        for sgn in (-1, 1):
            p.blob(bx + sgn * brx * 0.45, by + bry * 0.95, brx * 0.28, bry * 0.14, BEAK, 5)
    for k in (-1, 0, 1):
        p.arc(*H(0.08 * k, -1.0), 0.12 * hr, 0.16 * hr, 180 + 30 * k, 300 + 30 * k, 5)
    p.blob(hx, hy, 1.08 * hr, 0.98 * hr, PENG, 8, ang=tilt, k=2.5)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.36, 0.05), 0.42 * hr, 0.48 * hr, WHITE, 0, ang=tilt)
    p.blob(*H(0, 0.38), 0.6 * hr, 0.42 * hr, WHITE, 0, ang=tilt)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    p.shape([H(-0.18, 0.3), H(0, 0.2), H(0.18, 0.3), H(0, 0.44)], BEAK, 4)
    _limbs(p, arms, PENG, 13)


def mochi(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), ribbon=True):
    """여친 후보: 모찌 (말랑한 찹쌀떡, 몸 전체가 얼굴). body는 무시, 짧은 발만."""
    H = _H(hx, hy, hr, tilt)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.48, 0.86), 0.2 * hr, 0.14 * hr, MOCHI, 6)
    p.blob(hx, hy, 1.28 * hr, 0.86 * hr, MOCHI, 8, ang=tilt, k=0.2, irr=0.015)
    for dx, dy in ((-0.9, -0.3), (0.85, -0.42), (-0.55, -0.62), (0.4, -0.7), (1.0, 0.15)):
        p.blob(*H(dx, dy), 0.04 * hr, 0.04 * hr, WHITE, 0)
    if ribbon:
        bow(p, *H(0.45, -0.78), 0.34 * hr, tilt + 15)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    _limbs(p, arms, MOCHI, 12)


def potato(p, hx, hy, hr, tilt=0, eyes="dot", mouth="flat", extras=(), body=None, arms=(), sprout=True):
    """남친 후보: 감자 (울퉁불퉁, 점박이, 머리 위 새싹). 몸 전체가 얼굴."""
    H = _H(hx, hy, hr, tilt)
    for sgn in (-1, 1):
        p.capsule(H(sgn * 0.4, 0.8), H(sgn * 0.5, 1.2), 0.13 * hr, 0.15 * hr, POTATO, 6)
    if sprout:
        p.line([H(0.05, -1.0), H(0.1, -1.32)], 6, (90, 150, 70))
        p.blob(*H(-0.12, -1.38), 0.2 * hr, 0.1 * hr, LEAF, 5, ang=tilt - 25)
        p.blob(*H(0.32, -1.36), 0.2 * hr, 0.1 * hr, LEAF, 5, ang=tilt + 25)
    p.blob(hx, hy, 1.02 * hr, 1.12 * hr, POTATO, 8, ang=tilt, irr=0.06, k=3.3)
    for dx, dy, r in ((-0.6, -0.55, 0.07), (0.55, -0.7, 0.05), (0.75, 0.5, 0.06), (-0.7, 0.65, 0.05), (0.1, -0.85, 0.04)):
        p.blob(*H(dx, dy), r * hr, r * hr * 0.8, POTATO_D, 0)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    _limbs(p, arms, POTATO, 13)


CHARACTERS = {"bunny": bunny, "bear": bear, "cat": cat, "dog": dog, "hamster": hamster,
              "penguin": penguin, "mochi": mochi, "potato": potato}


# ---------------- 추가 캐릭터 2차 (인스타 감성 시안) ----------------
RICE = (255, 255, 252)
GIM = (38, 66, 48)
PEACH = (255, 190, 170)
PEACH_D = (255, 140, 130)
SWEETPOTATO = (176, 72, 112)
BREAD = (255, 234, 184)
CRUST = (204, 142, 72)
BUTTER = (255, 226, 92)
BUTTER_T = (255, 240, 150)
DUMPLING = (252, 246, 228)
BUN = (255, 251, 242)
CLOUD = (232, 243, 255)
BOLT = (255, 214, 40)


def _eye_whites(p, H, hr, r=0.17):
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.36, 0.02), r * hr, r * 1.15 * hr, WHITE, 0)


def rice(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), ribbon=True):
    """밥풀: 길쭉한 흰 쌀알 + 반짝 하이라이트."""
    H = _H(hx, hy, hr, tilt)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.35, 1.1), 0.16 * hr, 0.1 * hr, RICE, 5)
    p.blob(hx, hy, 0.88 * hr, 1.14 * hr, RICE, 8, ang=tilt, k=0.9)
    p.arc(*H(-0.42, -0.35), 0.18 * hr, 0.4 * hr, 200, 250, 5, ang=tilt, color=(205, 220, 235))
    if ribbon:
        bow(p, *H(0.35, -1.02), 0.3 * hr, tilt + 15)
    face(p, hx, hy + 0.08 * hr, hr * 0.92, tilt, eyes, mouth, extras)
    _limbs(p, arms, RICE, 11)


def gim(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=()):
    """김: 바삭한 네모 김 (참깨 점). 어두운 얼굴이라 눈 흰자를 깔아준다."""
    H = _H(hx, hy, hr, tilt)
    for sgn in (-1, 1):
        p.capsule(H(sgn * 0.45, 0.85), H(sgn * 0.5, 1.2), 0.1 * hr, 0.12 * hr, GIM, 5)
    pts = [H(-0.95, -0.95), H(0.0, -1.02), H(0.95, -0.95), H(1.0, 0.0), H(0.95, 0.95), H(0, 1.0), H(-0.95, 0.95), H(-1.02, 0)]
    p.shape(pts, GIM, 8)
    for dx, dy in ((-0.6, -0.65), (0.5, -0.72), (0.72, 0.62), (-0.7, 0.68)):
        p.blob(*H(dx, dy), 0.05 * hr, 0.03 * hr, (250, 240, 200), 0, ang=tilt + 30)
    _eye_whites(p, H, hr)
    p.blob(*H(0, 0.5), 0.17 * hr, 0.12 * hr, WHITE, 0)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    _limbs(p, arms, GIM, 11)


def peach(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), ribbon=False):
    """복숭아: 엉덩이 골 + 잎사귀. 몸개그용."""
    H = _H(hx, hy, hr, tilt)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.42, 0.98), 0.16 * hr, 0.1 * hr, PEACH, 5)
    p.blob(*H(0.32, -1.02), 0.32 * hr, 0.14 * hr, LEAF, 6, ang=tilt - 25)
    p.blob(hx, hy, 1.08 * hr, 1.0 * hr, PEACH, 8, ang=tilt, k=1.9)
    p.blob(*H(0.2, 0.25), 0.7 * hr, 0.6 * hr, (255, 170, 160), 0, ang=tilt)
    p.arc(*H(0.02, -0.98), 0.3 * hr, 0.55 * hr, 60, 110, 6, ang=tilt)
    if ribbon:
        bow(p, *H(-0.4, -0.92), 0.28 * hr, tilt - 15)
    face(p, hx, hy + 0.05 * hr, hr, tilt, eyes, mouth, extras)
    _limbs(p, arms, PEACH, 11)


def sweetpotato(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=()):
    """고구마: 길쭉 비스듬, 꼬리 뿌리, 자주색."""
    H = _H(hx, hy, hr, tilt)
    p.line([H(0.25, 1.05), H(0.45, 1.35), H(0.4, 1.5)], 5, (120, 80, 60))
    for sgn in (-1, 1):
        p.capsule(H(sgn * 0.42, 0.85), H(sgn * 0.5, 1.15), 0.11 * hr, 0.13 * hr, SWEETPOTATO, 5)
    p.blob(hx, hy, 0.86 * hr, 1.16 * hr, SWEETPOTATO, 8, ang=tilt + 12, irr=0.05, k=4.1)
    for dx, dy in ((-0.45, -0.6), (0.4, -0.85), (0.55, 0.55)):
        p.arc(*H(dx, dy), 0.1 * hr, 0.05 * hr, 0, 180, 4, ang=tilt, color=(120, 40, 80))
    _eye_whites(p, H, hr, 0.15)
    face(p, hx, hy, hr * 0.92, tilt, eyes, mouth, extras)
    _limbs(p, arms, SWEETPOTATO, 11)


def toast(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), ribbon=True):
    """식빵: 위가 볼록한 빵 단면 + 갈색 테두리(크러스트)."""
    H = _H(hx, hy, hr, tilt)

    def slice_pts(sc):
        pts = []
        for i in range(19):          # 위쪽 두 혹
            a = math.pi + math.pi * i / 18
            pts.append(H(-0.5 * sc + 0.48 * sc * math.cos(a), -0.45 * sc + 0.5 * sc * math.sin(a)))
        for i in range(19):
            a = math.pi + math.pi * i / 18
            pts.append(H(0.5 * sc + 0.48 * sc * math.cos(a), -0.45 * sc + 0.5 * sc * math.sin(a)))
        pts += [H(0.92 * sc, 0.95 * sc), H(-0.92 * sc, 0.95 * sc)]
        return pts
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.42, 1.05), 0.15 * hr, 0.09 * hr, BREAD, 5)
    p.shape(slice_pts(1.0), CRUST, 8)
    p.shape(slice_pts(0.82), BREAD, 0)
    if ribbon:
        bow(p, *H(-0.5, -0.95), 0.3 * hr, tilt - 10)
    face(p, hx, hy + 0.12 * hr, hr * 0.95, tilt, eyes, mouth, extras)
    _limbs(p, arms, BREAD, 11)


def butter(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), melt=0.0):
    """버터: 노란 큐브. melt(0~1)만큼 아래로 녹아 흐른다 (설렘 표현)."""
    H = _H(hx, hy, hr, tilt)
    if melt > 0:
        p.blob(*H(0, 0.95 + 0.1 * melt), (1.0 + 0.4 * melt) * hr, (0.16 + 0.12 * melt) * hr, BUTTER_T, 6)
        for dx in (-0.55, 0.1, 0.6):
            p.capsule(H(dx, 0.7), H(dx, 0.85 + 0.35 * melt), 0.09 * hr, 0.11 * hr, BUTTER, 5)
    p.shape([H(-0.85, -0.55), H(-0.45, -0.95), H(0.95, -0.95), H(0.55, -0.55)], BUTTER_T, 7)
    p.shape([H(0.55, -0.55), H(0.95, -0.95), H(0.95, 0.55), H(0.55, 0.92)], (240, 200, 60), 7)
    p.shape([H(-0.85, -0.55), H(0.55, -0.55), H(0.55, 0.92), H(-0.85, 0.92)], BUTTER, 7)
    face(p, hx - 0.15 * hr, hy + 0.15 * hr, hr * 0.85, tilt, eyes, mouth, extras)
    _limbs(p, arms, BUTTER, 11)


def wonky(p, hx, hy, hr, tilt=0, eyes="dot", mouth="w", extras=(), body=None, arms=(), kind="cat"):
    """하찮은 B급: 흰 몸, 삐뚤빼뚤 두꺼운 선, 작은 점눈. kind=cat|dog."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        p.blob(bx, by, brx * 0.9, bry, WHITE, 9, irr=0.08, k=5.5)
    if kind == "cat":
        for sgn in (-1, 1):
            p.shape([H(sgn * 0.75, -0.45), H(sgn * 0.3, -0.8), H(sgn * 0.68, -1.15)], WHITE, 9)
    p.blob(hx, hy, 1.05 * hr, 0.92 * hr, WHITE, 9, ang=tilt, irr=0.09, k=2.7 if kind == "cat" else 6.1)
    if kind == "dog":
        for sgn in (-1, 1):
            p.blob(*H(sgn * 0.9, 0.05), 0.17 * hr, 0.36 * hr, WHITE, 9, ang=tilt + sgn * 20, irr=0.08, k=sgn)
    small = {"dot": "dot"}.get(eyes, eyes)
    face(p, hx, hy + 0.06 * hr, hr * 0.8, tilt, small, mouth, extras)
    _limbs(p, arms, WHITE, 13)


def dumpling(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), ribbon=True):
    """만두: 반달 모양 + 윗선 주름."""
    H = _H(hx, hy, hr, tilt)
    pts = []
    for a in range(0, 360, 10):
        sn = math.sin(math.radians(a))
        dy = 0.35 - 1.05 * sn if a <= 180 else 0.35 + 0.38 * abs(sn)
        pts.append(H(1.25 * math.cos(math.radians(a)), dy))
    p.shape(pts, DUMPLING, 8)
    for k in range(-2, 3):
        p.arc(*H(0.32 * k, -0.42 + 0.1 * abs(k)), 0.13 * hr, 0.2 * hr, 200, 340, 5, ang=tilt + 8 * k)
    if ribbon:
        bow(p, *H(0.75, -0.5), 0.28 * hr, tilt + 25)
    face(p, hx, hy + 0.22 * hr, hr * 0.85, tilt, eyes, mouth, extras)
    _limbs(p, arms, DUMPLING, 11)


def steamed_bun(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=()):
    """찐빵: 동글 납작 + 정수리 팥 점."""
    H = _H(hx, hy, hr, tilt)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.45, 0.9), 0.16 * hr, 0.1 * hr, BUN, 5)
    p.blob(hx, hy, 1.15 * hr, 0.92 * hr, BUN, 8, ang=tilt, k=3.7)
    p.blob(*H(0, -0.78), 0.14 * hr, 0.1 * hr, (120, 50, 50), 4)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    _limbs(p, arms, BUN, 11)


def cloud(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), rain=0, t=0, ribbon=True):
    """구름: 뭉게뭉게. rain>0 이면 눈물비가 내린다 (슬픔 표현)."""
    H = _H(hx, hy, hr, tilt)
    puffs = [(-0.75, 0.15, 0.48), (-0.35, -0.42, 0.55), (0.3, -0.5, 0.6), (0.8, 0.05, 0.5), (0.0, 0.25, 0.85)]
    for dx, dy, r in puffs:
        p.blob(*H(dx, dy), r * hr, r * 0.92 * hr, CLOUD, 8, k=dx * 3)
    for dx, dy, r in puffs:
        p.blob(*H(dx, dy), r * hr * 0.9, r * 0.92 * hr * 0.88, CLOUD, 0)
    for i in range(rain):
        x = -0.6 + 1.2 * i / max(1, rain - 1)
        y = 1.05 + ((t * 0.12 + i * 0.37) % 0.6)
        p.shape([H(x, y - 0.1), H(x + 0.06, y + 0.04), H(x, y + 0.1), H(x - 0.06, y + 0.04)], TEAR, 3)
    if ribbon:
        bow(p, *H(-0.4, -0.85), 0.28 * hr, tilt - 15)
    face(p, hx, hy + 0.1 * hr, hr * 0.85, tilt, eyes, mouth, extras)
    _limbs(p, arms, CLOUD, 11)


def bolt(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), flash=False):
    """번개: 노란 동그라미 + 지그재그 번개 머리. flash면 번쩍 효과."""
    H = _H(hx, hy, hr, tilt)
    if flash:
        for k in range(8):
            a = 2 * math.pi * k / 8
            p.line([H(1.25 * math.cos(a), 1.2 * math.sin(a)), H(1.55 * math.cos(a), 1.5 * math.sin(a))], 5, SPARK)
    p.shape([H(-0.2, -0.75), H(0.15, -1.45), H(0.05, -1.05), H(0.38, -1.12), H(0.1, -0.7)], BOLT, 6)
    for sgn in (-1, 1):
        p.capsule(H(sgn * 0.45, 0.85), H(sgn * 0.5, 1.18), 0.11 * hr, 0.13 * hr, BOLT, 5)
    p.blob(hx, hy, 1.05 * hr, 0.95 * hr, BOLT, 8, ang=tilt, k=0.3)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    _limbs(p, arms, BOLT, 11)


CHARACTERS.update({"rice": rice, "gim": gim, "peach": peach, "sweetpotato": sweetpotato,
                   "toast": toast, "butter": butter, "wonky": wonky, "dumpling": dumpling,
                   "steamed_bun": steamed_bun, "cloud": cloud, "bolt": bolt})


# ---------------- 추가 캐릭터 3차 (다른 결: 사람·막대·유령·공룡·바다·몬스터) ----------------
SKIN = (255, 226, 204)
HAIR = (78, 54, 44)
DRESS = (255, 150, 182)
SHIRT = (112, 162, 232)
GHOST = (250, 250, 255)
REX = (255, 168, 190)
STEGO = (140, 206, 128)
SEAL = (222, 228, 238)
OCTO = (255, 132, 96)
HORNMON = (196, 160, 240)
FURMON = (120, 214, 170)


def human(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), gender="girl"):
    """사람 2등신: 여친은 똥머리+단발+원피스, 남친은 짧은 머리+티셔츠."""
    H = _H(hx, hy, hr, tilt)
    top = DRESS if gender == "girl" else SHIRT
    if body:
        bx, by, brx, bry = body
        for sgn in (-1, 1):
            p.capsule((bx + sgn * brx * 0.4, by + bry * 0.6), (bx + sgn * brx * 0.45, by + bry * 1.25), 11, 13, SKIN)
        if gender == "girl":
            p.shape([(bx - brx * 0.55, by - bry * 0.9), (bx + brx * 0.55, by - bry * 0.9),
                     (bx + brx * 1.05, by + bry * 0.85), (bx - brx * 1.05, by + bry * 0.85)], top, 7)
        else:
            p.blob(bx, by, brx * 0.85, bry, top, 7)
    if gender == "girl":
        p.blob(*H(0, 0.12), 1.16 * hr, 1.05 * hr, HAIR, 8, ang=tilt)
        p.blob(*H(0, -1.08), 0.34 * hr, 0.3 * hr, HAIR, 7)
    p.blob(hx, hy, 1.0 * hr, 0.95 * hr, SKIN, 8, ang=tilt, k=0.5)
    pts = [H(1.04 * math.cos(math.radians(a)), 0.98 * math.sin(math.radians(a))) for a in range(185, 356, 10)]
    if gender == "girl":
        pts += [H(0.85, -0.3), H(0.5, -0.42), H(0.3, -0.3), H(0.0, -0.45), H(-0.3, -0.32), H(-0.6, -0.42), H(-0.9, -0.25)]
        p.shape(pts, HAIR, 7)
        bow(p, *H(0.38, -1.12), 0.28 * hr, tilt + 15)
    else:
        pts += [H(0.9, -0.35), H(0.6, -0.5), H(0.35, -0.38), H(0.1, -0.52), H(-0.2, -0.4), H(-0.5, -0.52), H(-0.88, -0.35)]
        p.shape(pts, HAIR, 7)
        p.line([H(0.05, -0.98), H(0.15, -1.2)], 5, HAIR)
    face(p, hx, hy + 0.1 * hr, hr * 0.92, tilt, eyes, mouth, extras)
    _limbs(p, arms, SKIN, 10)


def stick(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), gender="girl", legs=None):
    """막대인간: 동그란 머리 + 선 몸통/팔다리. arms=[(손끝)] 은 어깨에서 그 점까지 선."""
    H = _H(hx, hy, hr, tilt)
    neck = H(0, 1.0)
    hip = (neck[0], neck[1] + 1.5 * hr)
    p.line([neck, hip], 6)
    for (ax, ay) in (arms or [(neck[0] - 0.9 * hr, neck[1] + 1.0 * hr), (neck[0] + 0.9 * hr, neck[1] + 1.0 * hr)]):
        p.line([(neck[0], neck[1] + 0.35 * hr), (ax, ay)], 6)
    for (lx, ly) in (legs or [(hip[0] - 0.55 * hr, hip[1] + 1.2 * hr), (hip[0] + 0.55 * hr, hip[1] + 1.2 * hr)]):
        p.line([hip, (lx, ly)], 6)
    p.blob(hx, hy, hr, hr, WHITE, 7, ang=tilt)
    if gender == "girl":
        bow(p, *H(0.45, -0.9), 0.3 * hr, tilt + 20)
    else:
        p.arc(*H(0.05, -1.08), 0.12 * hr, 0.16 * hr, 180, 320, 5, ang=tilt)
    face(p, hx, hy, hr * 0.85, tilt, eyes, mouth, extras)


def ghost(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), ribbon=False, halo=False):
    """유령: 위는 둥글고 아래는 물결 꼬리. halo면 천사 고리."""
    H = _H(hx, hy, hr, tilt)
    if halo:
        p.blob(*H(0, -1.25), 0.5 * hr, 0.14 * hr, None, 6, color=SPARK)
    pts = [H(1.0 * math.cos(math.radians(a)), 1.0 * math.sin(math.radians(a))) for a in range(180, 361, 10)]
    pts += [H(1.0, 0.6), H(1.05, 1.15)]
    for i in range(6):
        x = 1.05 - (i + 1) * 0.35
        pts.append(H(x + 0.17, 1.15 - 0.22 * (i % 2 == 0)))
        pts.append(H(x, 1.15))
    pts += [H(-1.0, 0.6)]
    p.shape(pts, GHOST, 8)
    p.blob(*H(0.55, 0.75), 0.28 * hr, 0.18 * hr, (226, 232, 250), 0)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 1.0, 0.35), 0.2 * hr, 0.13 * hr, GHOST, 6, ang=tilt + sgn * 30)
    if ribbon:
        bow(p, *H(0.4, -0.92), 0.3 * hr, tilt + 15)
    face(p, hx, hy - 0.05 * hr, hr * 0.9, tilt, eyes, mouth, extras)


def dino(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=(), kind="rex", ribbon=False):
    """공룡: rex(분홍, 짧은 팔) / stego(초록, 등 판)."""
    H = _H(hx, hy, hr, tilt)
    col = REX if kind == "rex" else STEGO
    plate = (255, 120, 150) if kind == "rex" else (250, 210, 80)
    if body:
        bx, by, brx, bry = body
        p.capsule((bx + brx * 0.6, by + bry * 0.5), (bx + brx * 1.6, by + bry * 0.9), 0.32 * brx, 0.1 * brx, col)
        for sgn in (-1, 1):
            p.capsule((bx + sgn * brx * 0.45, by + bry * 0.6), (bx + sgn * brx * 0.5, by + bry * 1.15), 14, 16, col)
        p.blob(bx, by, brx, bry, col, 7)
        p.blob(bx, by + bry * 0.15, brx * 0.6, bry * 0.65, (255, 240, 220), 0)
    for k, (dx, dy) in enumerate(((-0.55, -0.85), (0.0, -1.02), (0.55, -0.85))):
        b0, b1 = H(dx - 0.18, dy + 0.14), H(dx + 0.18, dy + 0.14)
        tip = H(dx * 1.15, dy - 0.38)
        p.shape([b0, tip, b1], plate, 6)
    p.blob(hx, hy, 1.1 * hr, 0.95 * hr, col, 8, ang=tilt, k=1.6)
    if ribbon:
        bow(p, *H(-0.75, -0.65), 0.28 * hr, tilt - 25)
    face(p, hx, hy + 0.05 * hr, hr, tilt, eyes, mouth, extras)
    if kind == "rex" and body:
        bx, by, brx, bry = body
        for sgn in (-1, 1):
            p.capsule((bx + sgn * brx * 0.45, by - bry * 0.35), (bx + sgn * brx * 0.62, by - bry * 0.15), 9, 9, col, 5)
    _limbs(p, arms, col, 13)


def seal(p, hx, hy, hr, tilt=0, eyes="dot", mouth="w", extras=(), body=None, arms=(), ribbon=True):
    """물범: 회백색 몽실 몸 + 점박이 + 수염 점, 지느러미 꼬리."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        p.blob(bx + brx * 1.05, by + bry * 0.55, brx * 0.42, bry * 0.22, SEAL, 6, ang=-25)
        p.blob(bx, by, brx * 1.15, bry * 0.8, SEAL, 7)
        for dx, dy in ((-0.4, -0.2), (0.3, 0.1), (0.6, -0.35)):
            p.blob(bx + dx * brx, by + dy * bry, 7, 6, (170, 180, 195), 0)
    p.blob(hx, hy, 1.08 * hr, 0.98 * hr, SEAL, 8, ang=tilt, k=0.9)
    for dx, dy in ((-0.7, -0.5), (0.65, -0.62), (0.1, -0.8)):
        p.blob(*H(dx, dy), 0.06 * hr, 0.05 * hr, (170, 180, 195), 0)
    if ribbon:
        bow(p, *H(0.5, -0.9), 0.3 * hr, tilt + 15)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    for sgn in (-1, 1):
        for k in range(3):
            p.blob(*H(sgn * (0.2 + 0.08 * k), 0.5 + 0.05 * (k % 2)), 0.02 * hr, 0.02 * hr, INK, 0)
    _limbs(p, arms, SEAL, 13)


def octopus(p, hx, hy, hr, tilt=0, eyes="dot", mouth="o", extras=(), body=None, arms=(), t=0, blush_body=False):
    """문어: 둥근 머리 + 물결 다리 4개. blush_body면 부끄러워 온몸이 빨개짐."""
    H = _H(hx, hy, hr, tilt)
    col = (255, 90, 90) if blush_body else OCTO
    for i, sgn in enumerate((-1.2, -0.45, 0.45, 1.2)):
        pts = []
        for k in range(9):
            f = k / 8
            pts.append(H(sgn * (0.55 + 0.45 * f) + 0.12 * math.sin(f * 5 + t * 0.8 + i), 0.6 + 0.9 * f))
        p.stroke(pts, 0.36 * hr * 1.0, False, INK)
        p.stroke(pts, 0.36 * hr * 0.72, False, col)
    p.blob(hx, hy, 1.0 * hr, 1.05 * hr, col, 8, ang=tilt, k=2.2)
    p.blob(*H(-0.4, -0.55), 0.18 * hr, 0.12 * hr, (255, 200, 180), 0, ang=tilt - 30)
    face(p, hx, hy + 0.12 * hr, hr * 0.92, tilt, eyes, mouth, extras)
    _limbs(p, arms, col, 12)


def monster(p, hx, hy, hr, tilt=0, eyes="dot", mouth="grin", extras=(), body=None, arms=(), kind="horn"):
    """몬스터: horn(라일락, 작은 뿔 + 송곳니) / fur(민트, 털 삐죽 + 외눈)."""
    H = _H(hx, hy, hr, tilt)
    col = HORNMON if kind == "horn" else FURMON
    for sgn in (-1, 1):
        p.capsule(H(sgn * 0.45, 0.82), H(sgn * 0.5, 1.2), 0.12 * hr, 0.14 * hr, col, 5)
    if kind == "horn":
        for sgn in (-1, 1):
            p.shape([H(sgn * 0.62, -0.62), H(sgn * 0.78, -1.25), H(sgn * 0.3, -0.85)], (255, 246, 214), 6)
        p.blob(hx, hy, 1.05 * hr, 0.98 * hr, col, 8, ang=tilt, k=3.1)
        face(p, hx, hy, hr, tilt, eyes, mouth, extras)
        p.shape([H(0.12, 0.47), H(0.22, 0.47), H(0.17, 0.62)], WHITE, 3)
    else:
        n = 26
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            r = 1.08 if i % 2 == 0 else 0.92
            pts.append(H(r * math.cos(a), r * 0.98 * math.sin(a)))
        p.shape(pts, col, 7)
        ex, ey = H(0, -0.05)
        if eyes == "heart":
            p.heart(ex, ey, 0.32 * hr, (255, 60, 110), 5)
        elif eyes in ("closed", "happy"):
            p.arc(ex, ey + (0.06 * hr if eyes == "happy" else -0.05 * hr), 0.25 * hr, 0.18 * hr,
                  200 if eyes == "happy" else 20, 340 if eyes == "happy" else 160, 6)
        else:
            p.blob(ex, ey, 0.34 * hr, 0.36 * hr, WHITE, 6)
            p.blob(ex + 0.04 * hr, ey + 0.06 * hr, 0.18 * hr, 0.2 * hr, INK, 0)
            p.blob(ex - 0.06 * hr, ey - 0.05 * hr, 0.07 * hr, 0.07 * hr, WHITE, 0)
        face(p, hx, hy + 0.1 * hr, hr, tilt, "none", mouth, extras)
    _limbs(p, arms, col, 12)


CHARACTERS.update({"human": human, "stick": stick, "ghost": ghost, "dino": dino,
                   "seal": seal, "octopus": octopus, "monster": monster})


# ---------------- 토끼 화풍 그대로의 새 커플 (다람쥐·너구리, 양·알파카, 판다·레서판다, 병아리·오리) ----------------
SQ = (214, 140, 80)
SQ_L = (250, 222, 180)
RAC = (156, 156, 168)
RAC_D = (78, 76, 90)
WOOL = (255, 255, 252)
SHEEP_F = (255, 236, 222)
ALPA = (246, 228, 196)
PANDA_K = (52, 48, 56)
RP = (214, 92, 52)
CHICK = (255, 218, 70)
DUCK_BILL = (255, 160, 40)


def _girl_bow(p, H, hr, tilt, dx=0.05, dy=-0.86, s=1.0):
    bow(p, *H(dx, dy), 0.4 * hr * s, tilt)


def squirrel(p, hx, hy, hr, tilt=0, eyes="sparkle", mouth="smile", extras=("blush",), body=None, arms=(),
             cheeks=0.0, ribbon=True):
    """다람쥐 여친: 몸 뒤로 크게 말린 꼬리, 귀 끝 털, 도토리 볼."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        p.blob(bx + brx * 1.15, by - bry * 0.9, brx * 0.75, bry * 1.55, SQ, 8, ang=18, k=2.0)
        p.blob(bx + brx * 1.05, by - bry * 0.85, brx * 0.32, bry * 1.1, SQ_L, 0, ang=18)
        p.blob(bx, by, brx, bry, SQ, 7)
        p.blob(bx, by + bry * 0.12, brx * 0.6, bry * 0.65, SQ_L, 0)
    for sgn in (-1, 1):
        p.shape([H(sgn * 0.78, -0.5), H(sgn * 0.35, -0.85), H(sgn * 0.72, -1.3)], SQ, 7)
        p.line([H(sgn * 0.72, -1.3), H(sgn * 0.8, -1.48)], 5)
        p.shape([H(sgn * 0.66, -0.62), H(sgn * 0.46, -0.82), H(sgn * 0.66, -1.08)], BUNNY_IN, 0)
    p.blob(hx, hy, 1.08 * hr, 0.95 * hr, SQ, 8, ang=tilt, k=1.0)
    p.blob(*H(0, 0.38), 0.62 * hr, 0.45 * hr, SQ_L, 0, ang=tilt)
    if cheeks:
        for sgn in (-1, 1):
            p.blob(*H(sgn * 0.66, 0.42), 0.2 * hr * (1 + cheeks), 0.17 * hr * (1 + cheeks), SQ_L, 6)
    if ribbon:
        _girl_bow(p, H, hr, tilt, 0.0, -0.9, 0.85)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    _limbs(p, arms, SQ, 16)


def raccoon(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=()):
    """너구리 남친: 눈가 검은 마스크, 줄무늬 꼬리."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        tail = [((bx + brx * 0.8, by + bry * 0.4)), ((bx + brx * 1.55, by - bry * 0.3))]
        p.capsule(tail[0], tail[1], 0.32 * brx, 0.38 * brx, RAC, 7)
        for k in (0.35, 0.7):
            x = tail[0][0] + (tail[1][0] - tail[0][0]) * k
            y = tail[0][1] + (tail[1][1] - tail[0][1]) * k
            p.blob(x, y, 0.12 * brx, 0.3 * brx, RAC_D, 0, ang=-40)
        p.blob(bx, by, brx, bry, RAC, 7)
        p.blob(bx, by + bry * 0.12, brx * 0.58, bry * 0.62, (232, 232, 236), 0)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.72, -0.7), 0.28 * hr, 0.28 * hr, RAC, 7)
        p.blob(*H(sgn * 0.72, -0.7), 0.13 * hr, 0.13 * hr, RAC_D, 0)
    p.blob(hx, hy, 1.08 * hr, 0.95 * hr, RAC, 8, ang=tilt, k=2.4)
    p.blob(*H(0, 0.4), 0.42 * hr, 0.3 * hr, (240, 240, 244), 0, ang=tilt)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.4, 0.04), 0.34 * hr, 0.24 * hr, RAC_D, 0, ang=tilt + sgn * 18)
        if eyes not in ("sparkle", "teary"):
            p.blob(*H(sgn * 0.36, 0.02), 0.13 * hr, 0.15 * hr, WHITE, 0)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras, muzzle=False)
    p.blob(*H(0, 0.3), 0.1 * hr, 0.07 * hr, INK, 0)
    _limbs(p, arms, RAC_D, 16)


def sheep(p, hx, hy, hr, tilt=0, eyes="sparkle", mouth="smile", extras=("blush",), body=None, arms=(), ribbon=True):
    """양 여친: 뭉게뭉게 양털 머리 + 몸, 옆으로 늘어진 귀."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        for k in range(10):
            a = 2 * math.pi * k / 10
            p.blob(bx + brx * 0.82 * math.cos(a), by + bry * 0.8 * math.sin(a), brx * 0.36, bry * 0.36, WOOL, 7)
        p.blob(bx, by, brx * 0.88, bry * 0.86, WOOL, 0)
    for k in range(9):
        a = math.pi * (1.05 + 0.9 * k / 8)
        p.blob(*H(1.0 * math.cos(a), -0.15 + 0.95 * math.sin(a)), 0.32 * hr, 0.3 * hr, WOOL, 7, k=k)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 1.02, 0.08), 0.3 * hr, 0.14 * hr, SHEEP_F, 7, ang=tilt + sgn * 20)
    p.blob(hx, hy + 0.08 * hr, 0.88 * hr, 0.82 * hr, SHEEP_F, 8, ang=tilt, k=0.3)
    for k in range(5):
        a = math.pi * (1.15 + 0.7 * k / 4)
        p.blob(*H(0.72 * math.cos(a), -0.1 + 0.7 * math.sin(a)), 0.22 * hr, 0.2 * hr, WOOL, 6, k=k + 3)
    if ribbon:
        _girl_bow(p, H, hr, tilt, 0.42, -0.98, 0.8)
    face(p, hx, hy + 0.12 * hr, hr * 0.92, tilt, eyes, mouth, extras)
    _limbs(p, arms, WOOL, 15)


def alpaca(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=()):
    """알파카 남친: 긴 목, 정수리 복슬 앞머리, 뾰족 귀."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        p.capsule((bx, by - bry * 0.3), H(0, 0.7), 0.42 * hr, 0.4 * hr, ALPA, 7)
        p.blob(bx, by, brx, bry, ALPA, 7)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.62, -0.95), 0.14 * hr, 0.32 * hr, ALPA, 7, ang=tilt + sgn * 12)
    p.blob(hx, hy, 0.95 * hr, 0.98 * hr, ALPA, 8, ang=tilt, k=1.3)
    for k in range(5):
        p.blob(*H(-0.42 + 0.21 * k, -0.85 - 0.08 * (k % 2)), 0.2 * hr, 0.18 * hr, WOOL, 6, k=k)
    face(p, hx, hy + 0.05 * hr, hr * 0.95, tilt, eyes, mouth, extras, muzzle=True)
    _limbs(p, arms, ALPA, 15)


def panda(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=("blush",), body=None, arms=(), ribbon=True):
    """판다 여친: 흰 얼굴 + 검은 귀·눈테·팔다리."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        for sgn in (-1, 1):
            p.blob(bx + sgn * brx * 0.45, by + bry * 0.85, brx * 0.3, bry * 0.22, PANDA_K, 6)
        p.blob(bx, by, brx, bry, WHITE, 7)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.75, -0.72), 0.3 * hr, 0.28 * hr, PANDA_K, 7)
    p.blob(hx, hy, 1.08 * hr, 0.95 * hr, WHITE, 8, ang=tilt, k=0.8)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.38, 0.06), 0.27 * hr, 0.34 * hr, PANDA_K, 0, ang=tilt + sgn * 30)
        if eyes not in ("sparkle", "teary"):
            p.blob(*H(sgn * 0.36, 0.02), 0.12 * hr, 0.14 * hr, WHITE, 0)
    if ribbon:
        _girl_bow(p, H, hr, tilt, 0.0, -0.9, 0.85)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    p.blob(*H(0, 0.3), 0.09 * hr, 0.06 * hr, INK, 0)
    _limbs(p, arms, PANDA_K, 16)


def red_panda(p, hx, hy, hr, tilt=0, eyes="dot", mouth="smile", extras=(), body=None, arms=()):
    """레서판다 남친: 적갈색, 흰 눈썹·주둥이·귀 안쪽, 줄무늬 꼬리."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        t0, t1 = (bx - brx * 0.8, by + bry * 0.5), (bx - brx * 1.6, by - bry * 0.2)
        p.capsule(t0, t1, 0.34 * brx, 0.38 * brx, RP, 7)
        for k in (0.35, 0.7):
            p.blob(t0[0] + (t1[0] - t0[0]) * k, t0[1] + (t1[1] - t0[1]) * k, 0.12 * brx, 0.32 * brx, (150, 60, 36), 0, ang=40)
        p.blob(bx, by, brx, bry, (120, 52, 40), 7)
    for sgn in (-1, 1):
        p.shape([H(sgn * 0.85, -0.45), H(sgn * 0.42, -0.85), H(sgn * 0.88, -1.15)], RP, 7)
        p.shape([H(sgn * 0.76, -0.58), H(sgn * 0.52, -0.8), H(sgn * 0.78, -0.98)], WHITE, 0)
    p.blob(hx, hy, 1.1 * hr, 0.95 * hr, RP, 8, ang=tilt, k=1.9)
    p.blob(*H(0, 0.42), 0.42 * hr, 0.3 * hr, WHITE, 0, ang=tilt)
    for sgn in (-1, 1):
        p.blob(*H(sgn * 0.36, -0.3), 0.12 * hr, 0.08 * hr, WHITE, 0)
        p.blob(*H(sgn * 0.75, 0.3), 0.2 * hr, 0.16 * hr, WHITE, 0)
    face(p, hx, hy, hr, tilt, eyes, mouth, extras)
    p.blob(*H(0, 0.3), 0.09 * hr, 0.06 * hr, INK, 0)
    _limbs(p, arms, (120, 52, 40), 16)


def chick(p, hx, hy, hr, tilt=0, eyes="sparkle", mouth="none", extras=("blush",), body=None, arms=(), ribbon=True,
          beak_open=False):
    """병아리 여친: 머리=몸 한 덩어리, 머리털 세 가닥, 작은 부리."""
    H = _H(hx, hy, hr, tilt)
    for sgn in (-1, 1):
        p.line([H(sgn * 0.3, 0.92), H(sgn * 0.32, 1.2)], 6, DUCK_BILL)
        p.line([H(sgn * 0.32, 1.2), H(sgn * 0.45, 1.25)], 5, DUCK_BILL)
    for k in (-1, 0, 1):
        p.arc(*H(0.1 * k, -1.02), 0.1 * hr, 0.16 * hr, 190 + 25 * k, 330 + 25 * k, 5)
    p.blob(hx, hy, 1.05 * hr, 1.0 * hr, CHICK, 8, ang=tilt, k=0.9)
    if ribbon:
        _girl_bow(p, H, hr, tilt, 0.45, -0.85, 0.75)
    face(p, hx, hy - 0.05 * hr, hr * 0.95, tilt, eyes, "none", extras)
    if beak_open:
        p.shape([H(-0.16, 0.3), H(0.16, 0.3), H(0, 0.42)], DUCK_BILL, 5)
        p.shape([H(-0.13, 0.46), H(0.13, 0.46), H(0, 0.56)], DUCK_BILL, 5)
    else:
        p.shape([H(-0.16, 0.3), H(0.16, 0.3), H(0, 0.48)], DUCK_BILL, 5)
    _limbs(p, arms, CHICK, 13)


def duck(p, hx, hy, hr, tilt=0, eyes="dot", mouth="none", extras=(), body=None, arms=()):
    """오리 남친: 흰 몸, 납작하고 넓은 주황 부리, 머리털 한 가닥."""
    H = _H(hx, hy, hr, tilt)
    if body:
        bx, by, brx, bry = body
        for sgn in (-1, 1):
            p.blob(bx + sgn * brx * 0.45, by + bry * 0.95, brx * 0.32, bry * 0.15, DUCK_BILL, 5)
        p.blob(bx, by, brx, bry, WHITE, 7)
    p.arc(*H(0.05, -1.0), 0.1 * hr, 0.18 * hr, 190, 320, 5)
    p.blob(hx, hy, 1.0 * hr, 0.95 * hr, WHITE, 8, ang=tilt, k=1.5)
    face(p, hx, hy - 0.08 * hr, hr, tilt, eyes, "none", extras)
    p.blob(*H(0, 0.42), 0.42 * hr, 0.17 * hr, DUCK_BILL, 6, ang=tilt)
    p.line([H(-0.3, 0.42), H(0.3, 0.42)], 3)
    _limbs(p, arms, WHITE, 15)


CHARACTERS.update({"squirrel": squirrel, "raccoon": raccoon, "sheep": sheep, "alpaca": alpaca,
                   "panda": panda, "red_panda": red_panda, "chick": chick, "duck": duck})


# ---------------- 소품 / 효과 (리빌형에서 추가) ----------------
PUFF = (214, 226, 140)


def puff(p, x, y, s=1.0, k=0.0):
    """방귀 구름."""
    for dx, dy, r in ((0, 0, 26), (-24, 8, 18), (22, 10, 20), (4, -18, 18)):
        p.blob(x + dx * s, y + dy * s, r * s, r * s * 0.9, PUFF, 5, k=k + dx)
    for dx, dy, r in ((0, 0, 24), (-24, 8, 16), (22, 10, 18), (4, -18, 16)):
        p.blob(x + dx * s, y + dy * s, r * s, r * s * 0.9, PUFF, 0)


def tag(p, x, y, text, size=34, fill=YELLOW):
    """컷 왼쪽 위 노란 태그 (예: '연애초: 방귀를 참음')."""
    w = p.text_w(text, size)
    p.shape([(x, y), (x + w + 40, y), (x + w + 40, y + size + 30), (x, y + size + 30)], fill, 6)
    p.text(x + 20, y + (size + 30) / 2 + 1, text, size, anchor="lm")


def side_label(p, x, y, lines, size=30, anchor="mm"):
    """컷 아래 구석 라벨 (예: '여친:' / '방구참기' / '3시간째')."""
    for i, s in enumerate(lines):
        p.text(x, y + i * (size + 8), s, size, anchor=anchor)


_bg_cache = {}


def _lerp(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def bg_gradient(w, h, c1, c2, c3=None):
    """대각선 파스텔 그라데이션 (+반짝 점). w,h는 1x 좌표."""
    key = ("grad", w, h, c1, c2, c3)
    if key in _bg_cache:
        return _bg_cache[key]
    W2, H2 = w * SS, h * SS
    small = Image.new("RGB", (64, 64))
    px = small.load()
    for yy in range(64):
        for xx in range(64):
            f = (xx + yy) / 126
            if c3 is None:
                px[xx, yy] = _lerp(c1, c2, f)
            else:
                px[xx, yy] = _lerp(c1, c2, f * 2) if f < 0.5 else _lerp(c2, c3, (f - 0.5) * 2)
    img = small.resize((W2, H2), Image.BICUBIC)
    glow = Image.new("RGB", (W2, H2), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    import random
    rnd = random.Random(7)
    for _ in range(26):
        cx, cy, r = rnd.uniform(0, W2), rnd.uniform(0, H2), rnd.uniform(4, 14) * SS
        g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(90, 90, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(6 * SS))
    from PIL import ImageChops
    img = ImageChops.add(img, glow)
    _bg_cache[key] = img
    return img


def bg_heart_glow(w, h, base=(255, 196, 222), edge=(255, 150, 196)):
    """핑크 배경 + 빛나는 하트 후광 (애정 장면용)."""
    key = ("heart", w, h, base, edge)
    if key in _bg_cache:
        return _bg_cache[key]
    W2, H2 = w * SS, h * SS
    small = Image.new("RGB", (64, 64))
    px = small.load()
    for yy in range(64):
        for xx in range(64):
            d = min(1.0, math.hypot((xx - 32) / 32, (yy - 32) / 32))
            px[xx, yy] = _lerp((255, 236, 244), edge, d ** 1.4)
    img = small.resize((W2, H2), Image.BICUBIC)
    glow = Image.new("RGB", (W2, H2), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    for sc, wd in ((0.42, 26), (0.3, 18)):
        pts = []
        for i in range(80):
            tt = 2 * math.pi * i / 80
            x = 16 * math.sin(tt) ** 3
            y = -(13 * math.cos(tt) - 5 * math.cos(2 * tt) - 2 * math.cos(3 * tt) - math.cos(4 * tt))
            pts.append((W2 / 2 + x * h * sc * SS / 16, H2 * 0.48 + y * h * sc * SS / 16))
        g.line(pts + [pts[0]], fill=(255, 255, 255), width=int(wd * SS), joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(10 * SS))
    from PIL import ImageChops
    img = ImageChops.add(img, ImageChops.multiply(glow, Image.new("RGB", (W2, H2), (200, 200, 200))))
    _bg_cache[key] = img
    return img


# ---------------- 위아래 2컷 리빌형 레이아웃 ----------------
RV_W, RV_H = 848, 487          # 컷 크기 (1x 좌표)
RV_X = 116
RV_Y = [520, 1095]
RV_TITLE_Y = (300, 430)


def _render_panel(ep, idx, t, alpha=1.0):
    fn, tag_text, bg = ep.PANELS[idx]
    img = bg(RV_W, RV_H).copy() if callable(bg) else Image.new("RGB", (RV_W * SS, RV_H * SS), bg or WHITE)

    def draw(p):
        fn(p, t)
        if tag_text:
            tag(p, -4, -4, tag_text)
        p.shape([(4, 4), (RV_W - 4, 3), (RV_W - 3, RV_H - 4), (3, RV_H - 3)], None, 10)

    style = getattr(ep, "STYLE", "marker")
    if style == "hand":
        import styles
        img = styles.render_hand(draw, RV_W, RV_H, t % 3, bg=img)
    elif style != "marker":
        import styles
        img = styles.render_variant(style, draw, RV_W, RV_H, t % 3, bg=img)
    else:
        draw(Pen(img, t % 3))
    if alpha < 1.0:
        img = Image.blend(Image.new("RGB", img.size, WHITE), img, alpha)
    return img


def render_frame_reveal(ep, t):
    style = getattr(ep, "STYLE", "marker")
    img = Image.new("RGB", (W * SS, H * SS), (253, 251, 246) if style == "hand" else WHITE)
    if style != "marker":
        import styles
        p = styles.make_pen(style, img, t % 3)
    else:
        p = Pen(img, t % 3)
    y0, y1 = RV_TITLE_Y
    p.shape([(RV_X - 10, y0), (RV_X + RV_W + 10, y0 - 3), (RV_X + RV_W + 12, y1), (RV_X - 12, y1 + 3)], YELLOW, 8)
    p.text(540, (y0 + y1) / 2 + 2, ep.TITLE, 52)

    reveal, fade = ep.REVEAL_AT, getattr(ep, "REVEAL_FADE", 5)
    n = getattr(ep, "N", N)
    img.paste(_render_panel(ep, 0, t), (RV_X * SS, RV_Y[0] * SS))
    if t >= reveal:
        a = min(1.0, (t - reveal + 1) / (fade + 1))
        a = min(a, (n - t) / 4) if n - t < 4 else a      # 루프 직전 살짝 페이드아웃
        img.paste(_render_panel(ep, 1, t, a), (RV_X * SS, RV_Y[1] * SS))
    return img.resize((W, H), Image.LANCZOS)


def render_episode(ep, out_dir, only=None):
    fdir = os.path.join(out_dir, "frames")
    os.makedirs(fdir, exist_ok=True)
    n = getattr(ep, "N", N)
    frames = [only] if only is not None else list(range(n))
    for t in frames:
        layout = getattr(ep, "LAYOUT", "grid")
        if layout == "pastel4":
            import mongle
            fn = mongle.render_frame_pastel4
        else:
            fn = {"slide": render_frame_slide, "reveal": render_frame_reveal}.get(layout, render_frame)
        fn(ep, t).save(os.path.join(fdir, f"f_{t:03d}.png"))
    return len(frames)
