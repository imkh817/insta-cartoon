"""에피소드: 우리 사이 방@귀 변천사 — 손그림 화풍 버전 (같은 컷, STYLE만 다름)."""
import importlib.util
import os

from cartoon import *  # noqa: F401,F403

_spec = importlib.util.spec_from_file_location(
    "fart_history", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fart_history.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

LAYOUT = "reveal"
STYLE = "hand"
TITLE = base.TITLE
VERSION = "손그림 화풍 시안"
FPS = base.FPS
REVEAL_AT = base.REVEAL_AT
REVEAL_FADE = base.REVEAL_FADE
N = base.N
PANELS = base.PANELS
