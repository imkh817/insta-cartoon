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
    p = Pen(img, t % 3)
    fn(p, t)
    if tag_text:
        tag(p, -4, -4, tag_text)
    p.shape([(4, 4), (RV_W - 4, 3), (RV_W - 3, RV_H - 4), (3, RV_H - 3)], None, 10)
    if alpha < 1.0:
        img = Image.blend(Image.new("RGB", img.size, WHITE), img, alpha)
    return img


def render_frame_reveal(ep, t):
    img = Image.new("RGB", (W * SS, H * SS), WHITE)
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
        fn = {"slide": render_frame_slide, "reveal": render_frame_reveal}.get(getattr(ep, "LAYOUT", "grid"), render_frame)
        fn(ep, t).save(os.path.join(fdir, f"f_{t:03d}.png"))
    return len(frames)
