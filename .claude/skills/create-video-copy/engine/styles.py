"""화풍(스타일) 모듈. cartoon.Pen을 상속해 선/면 처리를 바꾸고, 후처리로 질감을 입힌다.

사용: img = render_styled("sticker", draw_fn, w, h, boil)
  draw_fn(p) 는 로컬 좌표 (0..w, 0..h)에 장면을 그린다.
기존 cartoon.py 기본 화풍("marker")은 그대로 유지된다.
"""
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

import cartoon as C
from cartoon import INK, SS, WHITE

ACCENTS = {INK, C.MOUTH, C.RED, C.TONGUE, C.BLUSH, C.RIBBON, C.TEAR, C.SPARK,
           (255, 60, 110), (255, 80, 140), (255, 90, 130), (230, 60, 70)}


class StylePen(C.Pen):
    def __init__(self, img, boil, fill_map=None, fill_filter=None, line_color=None,
                 line_scale=1.0, var=1.0, line_on=True, passes=1, text_on=True):
        super().__init__(img, boil)
        self.fill_map = fill_map
        self.fill_filter = fill_filter
        self.line_color = line_color
        self.line_scale = line_scale
        self.var = var
        self.line_on = line_on
        self.passes = passes
        self.text_on = text_on

    def text(self, *a, **k):
        if self.text_on:
            super().text(*a, **k)

    def stroke(self, pts, w=7, closed=False, color=INK):
        if not self.line_on:
            return
        col = self.line_color if (self.line_color is not None and color == INK) else color
        P0 = [self.j(x, y) for x, y in pts]
        if closed:
            P0 = P0 + [P0[0]]
        self.seed += 1.7
        for ps in range(self.passes):
            off = (ps * 1.4 * SS, -ps * 0.9 * SS)
            P = [(x + off[0], y + off[1]) for x, y in P0]
            segs = list(zip(P, P[1:]))
            L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs) or 1
            step = 1.3 * SS
            sd = self.seed + self.boil * 0.9 + ps * 2.1
            base = w * self.line_scale * SS / 2 * (0.75 if ps else 1)
            v = self.var
            s = 0.0
            for (x0, y0), (x1, y1) in segs:
                l = math.hypot(x1 - x0, y1 - y0)
                n = max(1, int(l / step))
                for i in range(n):
                    f = i / n
                    x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                    ss = s + l * f
                    r = base * (1 - 0.2 * v + 0.2 * v * math.sin(ss * 0.018 + sd) + 0.1 * v * math.sin(ss * 0.07 + 2 * sd))
                    if not closed:
                        tp = min(1.0, ss / (8 * SS), (L - ss) / (8 * SS))
                        r *= 0.5 + 0.5 * max(0.0, tp)
                    r = max(r, 0.5)
                    self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)
                s += l

    def shape(self, pts, fill=None, w=7, color=INK):
        if fill is not None and (self.fill_filter is None or self.fill_filter(fill)):
            f = self.fill_map(fill) if self.fill_map else fill
            self.d.polygon([self.j(x, y) for x, y in pts], fill=f)
        if w:
            self.stroke(pts, w, True, color)


def _lighten(c, a):
    return tuple(int(v + (255 - v) * a) for v in c)


_grain = {}


def grain(size, lo=210, blur=0.7):
    key = (size, lo, blur)
    if key not in _grain:
        n = Image.frombytes("L", size, os.urandom(size[0] * size[1]))
        n = n.point(lambda v: lo + (255 - lo) * v // 255).filter(ImageFilter.GaussianBlur(blur))
        _grain[key] = Image.merge("RGB", (n, n, n))
    return _grain[key]


def _canvas(w, h, bg=WHITE):
    return Image.new("RGB", (w * SS, h * SS), bg)


def render_styled(style, draw, w, h, boil=0):
    """style: marker | line | crayon | sticker | watercolor | retro"""
    if style == "marker":
        img = _canvas(w, h)
        draw(C.Pen(img, boil))
        return img

    if style == "line":
        img = _canvas(w, h, (251, 249, 245))
        p = StylePen(img, boil, fill_map=lambda c: c if c in ACCENTS else (251, 249, 245),
                     line_scale=0.42, var=0.25)
        draw(p)
        return img

    if style == "crayon":
        img = _canvas(w, h, (251, 245, 231))
        p = StylePen(img, boil, fill_map=lambda c: c if c in ACCENTS else _lighten(c, 0.12),
                     line_color=(92, 62, 52), line_scale=0.62, var=2.2, passes=2)
        draw(p)
        return ImageChops.multiply(img, grain(img.size, 226, 0.8))

    if style == "sticker":
        layer = _canvas(w, h)
        draw(StylePen(layer, boil, line_scale=0.75, var=0.3))
        mask = ImageChops.difference(layer, Image.new("RGB", layer.size, WHITE)).convert("L").point(lambda v: 255 if v > 6 else 0)
        outline = mask.filter(ImageFilter.GaussianBlur(9 * SS)).point(lambda v: 255 if v > 10 else 0)
        shadow = outline.filter(ImageFilter.GaussianBlur(5 * SS))
        img = _canvas(w, h, (206, 236, 226))
        dots = ImageDraw.Draw(img)
        for yy in range(0, h * SS, 46 * SS):
            for xx in range(((yy // (46 * SS)) % 2) * 23 * SS, w * SS, 46 * SS):
                dots.ellipse([xx - 5 * SS, yy - 5 * SS, xx + 5 * SS, yy + 5 * SS], fill=(232, 248, 242))
        img.paste((120, 150, 140), (6 * SS, 9 * SS), ImageChops.offset(shadow, 0, 0).point(lambda v: v * 0.45))
        img.paste(WHITE, (0, 0), outline)
        img.paste(layer, (0, 0), mask.filter(ImageFilter.MaxFilter(3)))
        return img

    if style == "watercolor":
        fills = _canvas(w, h)
        draw(StylePen(fills, boil, fill_map=lambda c: _lighten(c, 0.18), line_on=False, text_on=False))
        fills = fills.filter(ImageFilter.GaussianBlur(3.5 * SS))
        fills = ImageChops.offset(fills, 4 * SS, 3 * SS)
        lines = _canvas(w, h)
        # 면은 흰색으로 칠해 뒤쪽 선을 가린다 (곱하기 합성이라 흰색은 영향 없음)
        draw(StylePen(lines, boil, fill_map=lambda c: c if c == INK else WHITE,
                      line_color=(118, 92, 92), line_scale=0.33, var=0.6))
        paper = Image.new("RGB", fills.size, (253, 250, 244))
        img = ImageChops.multiply(ImageChops.multiply(paper, fills), lines)
        return ImageChops.multiply(img, grain(img.size, 222, 1.6))

    if style == "retro":
        img = _canvas(w, h, (255, 214, 64))
        dd = ImageDraw.Draw(img)
        step = 22 * SS
        for yy in range(0, h * SS + step, step):
            for xx in range(0, w * SS + step, step):
                f = (xx / (w * SS) + yy / (h * SS)) / 2
                r = (2 + 7 * f) * SS
                dd.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(245, 120, 70))
        p = StylePen(img, boil, line_scale=1.35, var=0.35)
        draw(p)
        return ImageEnhance.Color(img).enhance(1.35)

    raise ValueError(style)


STYLES = ["marker", "line", "crayon", "sticker", "watercolor", "retro"]
