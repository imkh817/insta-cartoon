"""에피소드: 연애 1년차 vs 3년차 데이트 차이 — 1x1 슬라이드형 (컷이 사라지며 다음 컷 등장).

그림은 2x2 기준작(dating_1y_vs_3y.py)의 컷을 그대로 재사용한다.
"""
import importlib.util
import os

from cartoon import *  # noqa: F401,F403

_spec = importlib.util.spec_from_file_location(
    "dating_1y_vs_3y", os.path.join(os.path.dirname(os.path.abspath(__file__)), "dating_1y_vs_3y.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

LAYOUT = "slide"
TITLE = base.TITLE
VERSION = "슬라이드형 시안 v1"
TAG_COLORS = base.TAG_COLORS
FPS = 10
FRAMES_PER_SLIDE = 25           # 컷당 2.5초 (앞뒤 0.3초 페이드 포함)

# 같은 소재끼리 묶어 1년차 -> 3년차 순으로 비교
c = base.CELLS
SLIDES = [
    (c[0][0], "1년차", "데이트 준비: 풀메하고 설레며 등장"),
    (c[2][0], "3년차", "데이트 준비: 눈곱만 떼고 등장"),
    (c[1][0], "1년차", "영화 볼 때: 무서운 척 꼭 붙어있기"),
    (c[3][0], "3년차", "영화 볼 때: 오프닝 보고 동반 기절"),
]
N = FRAMES_PER_SLIDE * len(SLIDES)
