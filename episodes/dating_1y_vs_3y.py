"""에피소드: 연애 1년차 vs 3년차 데이트 차이 (2026-11 첫 완성작, 퀄리티 기준작)."""
import math

from cartoon import *  # noqa: F401,F403

TITLE = ["연애 1년차 vs 3년차", "데이트 차이"]
VERSION = "시안 v2"
FPS = 10
N = 96


def cut_1y_ready(p, t):
    ph = (t // 4) % 2
    tilt = -7 if ph else 7
    hx = 195 + (-4 if ph else 4)
    bunny(p, hx, 225, 100, tilt, "sparkle", "kiss", ("blush",), body=(195, 375, 72, 62),
          arms=[((165, 360), (138 + (-4 if ph else 4), 318)), ((225, 360), (252 + (-4 if ph else 4), 318))])
    spots = [[(55, 95, 26), (360, 60, 18), (60, 330, 16), (340, 210, 14)],
             [(70, 70, 16), (345, 85, 26), (45, 290, 22), (355, 240, 18)]]
    for x, y, s in spots[(t // 3) % 2]:
        p.sparkle(x, y, s)
    big = (t // 3) % 2
    bear(p, 395, 355, 55, -6, "heart", "o", ("blush+",))
    p.heart(440, 270 - 6 * big, 14 + 4 * big, (255, 60, 110), 4)
    p.text(370, 270, "두근", 26, (230, 60, 110))


def cut_1y_movie(p, t):
    sh = 3 if t % 2 else -3
    bob = (t // 6) % 2
    # 곰 (오른쪽)
    bear(p, 315, 205, 90, 4, "happy", "grin", ("blush+",), body=(310, 365, 85, 75),
         arms=[((370, 340), (405, 300))])
    popcorn(p, 420, 300, 0.8)
    # 토끼가 곰 팔에 매달림
    bunny(p, 165 + sh, 235, 85, 14, "teary", "wobbly", ("sweat",), body=(175 + sh, 378, 60, 55))
    p.capsule((250, 325), (240, 405), 18, 22, BEAR)
    p.capsule((200 + sh, 350), (262, 352), 15, 18, BUNNY)
    p.capsule((205 + sh, 385), (258, 390), 15, 18, BUNNY)
    for k in range(3):
        x = 55 + sh
        p.arc(x - 8 * k, 260, 12 + 8 * k, 26 + 8 * k, 120, 240, 4)
    p.heart(390, 85 - 6 * bob, 22 + 4 * bob, (255, 60, 110), 5)
    p.bubble(105, 70, "무서워잉..", 28, (130, 135))


def cut_3y_ready(p, t):
    yawn = (t // 12) % 2 == 0
    sc = (t // 3) % 2
    bunny(p, 195, 225, 100, -4, "half", "yawn" if yawn else "flat", ("boogers",), body=(200, 380, 78, 66),
          ribbon=False, ears="messy", body_fill=HOODIE,
          arms=[((250, 365), (225 + 10 * sc, 405 - 6 * sc)), ((145, 370), (125, 420))])
    for k in range(2 if sc else 3):
        p.line([(240 + 10 * k + 12 * sc, 385 - 6 * k), (255 + 10 * k + 12 * sc, 380 - 6 * k)], 4)
    bear(p, 395, 355, 55, 4, "down", "flat")
    p.shape([(365, 395), (415, 388), (420, 430), (370, 437)], (60, 60, 75), 6)
    p.text(330, 160, "하암~" if yawn else "", 30, (120, 120, 130))
    p.bubble(395, 255, "ㅇㅇ", 28, (400, 295))
    p.bubble(80, 175 if not yawn else 150, "가자", 30, (115, 210)) if not yawn else None


def cut_3y_movie(p, t):
    bob = 3 if (t // 6) % 2 else -3
    # 곰 (오른쪽, 고개 젖힘)
    bear(p, 305, 210 + bob, 88, -14, "closed", "o", (), body=(300, 365, 85, 75))
    r = 10 + 14 * (0.5 + 0.5 * math.sin(2 * math.pi * t / 24))
    p.blob(322 + r * 0.7, 250 + bob + r * 0.3, r, r, (205, 235, 255), 4)
    # 토끼 (왼쪽, 곰 어깨에 기댐)
    bunny(p, 160, 255 - bob, 82, 24, "closed", "drool", (), body=(165, 380, 62, 58), ribbon=False)
    popcorn(p, 420, 410, 0.7, tipped=True)
    for k, sz in enumerate((40, 32, 25)):
        ph = ((t + k * 8) % 24) / 24
        p.text(70 + k * 26 + ph * 14, 120 - k * 30 - ph * 30, "Z", sz, (110, 110, 135))


CELLS = [
    (cut_1y_ready, "1년차", "풀메하고 설레며 등장"),
    (cut_1y_movie, "1년차", "무서운 척 꼭 붙어있기"),
    (cut_3y_ready, "3년차", "눈곱만 떼고 등장"),
    (cut_3y_movie, "3년차", "오프닝 보고 동반 기절"),
]
TAG_COLORS = {"1년차": (235, 60, 120), "3년차": (110, 110, 125)}
