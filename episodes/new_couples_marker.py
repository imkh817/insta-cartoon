"""시안: 초반 토끼 화풍(마커) 그대로 그린 새 커플 4종. 2x2 그리드, 장면 + 루프 움직임."""
import math

from cartoon import *  # noqa: F401,F403

TITLE = ["토끼 화풍 그대로", "새 커플 시안 4종"]
VERSION = "캐릭터 시안 (마커 화풍)"
FPS = 10
N = 96


def cut_squirrel(p, t):
    chew = (t // 3) % 2
    squirrel(p, 150, 215, 82, -4, "happy", "smile", ("blush",), body=(150, 345, 62, 55),
             cheeks=0.35 + 0.15 * chew, arms=[((120, 330), (128, 300)), ((180, 330), (172, 300))])
    p.blob(150, 292, 13, 15, (170, 110, 60), 5)
    p.blob(150, 280, 15, 7, (120, 80, 50), 5)
    raccoon(p, 362, 225, 78, 6, "teary", "wobbly", (), body=(362, 350, 60, 54))
    p.bubble(380, 82, "한 입만..", 26, (365, 140))
    p.text(255, 120 - 4 * chew, "냠냠", 26, (150, 100, 60))


def cut_sheep(p, t):
    nuz = (t // 4) % 2
    sheep(p, 165, 238, 80, -6 + 4 * nuz, "happy", "smile", ("blush+",), body=(165, 365, 62, 52))
    alpaca(p, 330 - 6 * nuz, 205, 70, -16, "closed", "smile", ("blush",), body=(365, 375, 62, 50))
    for k in range(3):
        ph = ((t + k * 8) % 24) / 24
        p.heart(250 + 15 * k, 120 - ph * 60, 10 + 3 * k, (255, 60, 110), 4)
    p.text(165, 95, "부비부비", 26, (230, 80, 120))


def cut_panda(p, t):
    up = (t // 4) % 2
    panda(p, 150, 235, 80, 0, "happy", "o" if up else "smile", ("blush",), body=(150, 360, 64, 56),
          arms=[((175, 340), (205, 300))])
    p.line([(200, 330), (230, 250)], 9, (110, 180, 90))
    p.line([(200, 330), (230, 250)], 3)
    red_panda(p, 360, 215 - 6 * up, 74, 0, "squeeze", "wobbly", ("sweat",), body=(360, 345 - 6 * up, 58, 54),
              arms=[((325, 325 - 6 * up), (290, 230 - 25 * up)), ((395, 325 - 6 * up), (430, 230 - 25 * up))])
    p.bubble(360, 72, "흥!!", 28, (345, 120))


def cut_chick(p, t):
    hop = abs(math.sin(math.pi * (t % 8) / 8)) * 14
    chick(p, 175, 255 - hop, 76, 8, "closed", "none", ("blush+",), beak_open=False,
          arms=[((112, 262 - hop), (102, 240 - hop))])
    duck(p, 360, 232, 78, -4, "heart" if (t // 6) % 2 else "dot", "none", ("blush+",), body=(360, 358, 62, 55))
    p.bubble(150, 90, "쪽!", 30, (170, 160))
    p.heart(265, 150 - 6 * ((t // 4) % 2), 16, (255, 60, 110), 4)


CELLS = [
    (cut_squirrel, "다람쥐×너구리", "도토리 한 입만"),
    (cut_sheep, "양×알파카", "부비부비"),
    (cut_panda, "판다×레서판다", "질투 폭발"),
    (cut_chick, "병아리×오리", "뽀뽀 대작전"),
]
TAG_COLORS = {c[1]: (235, 60, 120) for c in CELLS}
