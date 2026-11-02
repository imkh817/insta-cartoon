"""에피소드: 우리 사이 뽀@뽀 변천사 — 병아리(여친) x 오리(남친), 얇은 마커, 위아래 2컷 리빌형.

연애초: 까치발로 쪽 -> 남친 심쿵 기절  /  현재: 뽀뽀 대신 부리 박치기 (반어적 애정)
"""
import math

from cartoon import *  # noqa: F401,F403

LAYOUT = "reveal"
STYLE = "thin"
TITLE = "우리 사이 뽀@뽀 변천사"
VERSION = "병아리x오리 · 얇은 마커 시안 v1"
FPS = 10
REVEAL_AT = 30
REVEAL_FADE = 5
N = 95


def cut_early(p, t):
    hop = abs(math.sin(math.pi * (t % 10) / 10)) * 16
    chick(p, 330, 265 - hop, 82, 12, "closed", "none", ("blush+",),
          arms=[((262, 262 - hop), (250, 228 - hop)), ((398, 262 - hop), (412, 228 - hop))])
    sway = -14 - 8 * math.sin(t * 0.5)
    duck(p, 565, 245, 84, sway, "closed", "none", ("blush+",), body=(572, 382, 64, 56))
    for k in range(3):
        ph = ((t + k * 7) % 21) / 21
        p.heart(610 + 22 * math.sin(ph * 6 + k), 150 - ph * 95, 11 + 3 * k, (255, 60, 110), 4)
    p.text(440, 205, "쪽", 34, (230, 60, 110))
    p.bubble(205, 115, "쪽♡", 30, (270, 185))
    p.bubble(700, 95, "(꼴깍)", 26, (640, 150))
    side_label(p, 88, 382, ["여친:", "까치발", "쪽"], 28)
    side_label(p, 770, 382, ["남친:", "심쿵", "기절"], 28)


def cut_now(p, t):
    lt = max(0, t - REVEAL_AT)
    hit = (lt // 5) % 2 == 1
    gap = 0 if hit else 22
    chick(p, 350 - gap, 268, 80, 14, "happy", "none", ("blush",),
          arms=[((282 - gap, 268), (268 - gap, 236))])
    duck(p, 505 + gap, 250, 84, -14, "happy", "none", ("blush",), body=(512 + gap, 396, 62, 55))
    if hit:
        p.sparkle(428, 168, 22)
        p.sparkle(462, 140, 13)
        p.text(430, 108, "콩!", 40, (230, 60, 110))
    p.bubble(195, 115, "콩!", 30, (290, 190))
    if lt >= 10:
        p.bubble(690, 95, "콩콩!", 30, (610, 160))
    side_label(p, 88, 382, ["여친:", "부리", "박치기"], 28)
    side_label(p, 775, 382, ["남친:", "마주", "박치기"], 28)


def bg_early(w, h):
    return bg_gradient(w, h, (214, 240, 250), (255, 248, 214), (255, 220, 232))


PANELS = [
    (cut_early, "연애초: 뽀뽀 한 번에 기절함", bg_early),
    (cut_now, "현재: 뽀뽀 대신 박치기함", bg_heart_glow),
]
