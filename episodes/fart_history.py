"""에피소드: 우리 사이 방@귀 변천사 (위아래 2컷 리빌형).

연애초: 방귀를 참음  ->  현재: 방귀로 대화함 (반어적 애정 결말)
"""
import math

from cartoon import *  # noqa: F401,F403

LAYOUT = "reveal"
TITLE = "우리 사이 방@귀 변천사"
VERSION = "리빌형 시안 v1"
FPS = 10
REVEAL_AT = 30          # 3초 뒤 아래 컷 등장
REVEAL_FADE = 5
N = 95                  # 9.5초 루프

RED_FACE = (255, 150, 160)


def cut_early(p, t):
    sh = 3 if t % 2 else -3
    # 여친: 방귀 참는 중 (얼굴 시뻘개짐, 덜덜)
    bunny(p, 300 + sh, 245, 90, 0, "squeeze", "wobbly", ("blush+",),
          body=(300 + sh, 388, 68, 58), face_fill=RED_FACE,
          arms=[((262 + sh, 372), (250 + sh, 420)), ((338 + sh, 372), (350 + sh, 420))])
    for k in range(3):
        p.arc(190 + sh - 9 * k, 300, 14 + 9 * k, 30 + 9 * k, 120, 240, 4)
        p.arc(410 + sh + 9 * k, 300, 14 + 9 * k, 30 + 9 * k, -60, 60, 4)
    drops = [(205, 175), (395, 160)] if (t // 3) % 2 else [(212, 195), (402, 180)]
    for x, y in drops:
        p.shape([(x, y - 16), (x + 9, y + 3), (x, y + 11), (x - 9, y + 3)], TEAR, 4)
    p.bubble(150, 125, "(꾸욱..)", 28, (225, 180))
    # 남친: 해맑게 모름
    bob = 3 if (t // 5) % 2 else 0
    bear(p, 600, 245 - bob, 90, 0, "dot", "o", (), body=(600, 390, 72, 62))
    p.text(690, 165 - bob, "?", 40, (90, 90, 110))
    p.bubble(735, 110, "왜 그랭?", 28, (665, 175))
    side_label(p, 85, 382, ["여친:", "방구참기", "3시간째"], 28)
    side_label(p, 768, 382, ["남친:", "해맑음"], 28)


def cut_now(p, t):
    lt = max(0, t - REVEAL_AT)
    sway = 5 if (t // 5) % 2 else -5
    bunny(p, 285, 252, 86, sway, "happy", "smile", ("blush",), body=(285, 390, 66, 56))
    bear(p, 575, 252, 86, -sway, "happy", "grin", ("blush",), body=(575, 392, 70, 60))
    # 뿡? -> 뿡! 주고받기
    s1 = 0.95 + 0.15 * math.sin(lt * 0.9)
    puff(p, 195, 420, s1, k=1)
    p.bubble(385, 105, "뿡?", 32, (320, 170))
    if lt >= 10:
        s2 = 0.95 + 0.15 * math.sin(lt * 0.9 + 1.5)
        puff(p, 668, 422, s2, k=2)
        p.bubble(690, 105, "뿡!", 32, (630, 170))
    for k in range(3):
        ph = ((t + k * 8) % 24) / 24
        p.heart(430 + 18 * math.sin(ph * 6 + k), 250 - ph * 90 + k * 12, 12 + 3 * k, (255, 80, 140), 4)
    side_label(p, 72, 300, ["여친:", "선빵 뿡"], 28)
    side_label(p, 780, 300, ["남친:", "화답 뿡"], 28)


def bg_early(w, h):
    return bg_gradient(w, h, (205, 242, 236), (255, 246, 214), (255, 214, 232))


PANELS = [
    (cut_early, "연애초: 방귀를 참음", bg_early),
    (cut_now, "현재: 방귀로 대화함", bg_heart_glow),
]
