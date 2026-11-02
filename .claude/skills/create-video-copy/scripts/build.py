"""에피소드 렌더링 + MP4/GIF 인코딩.

사용법:
  python3 build.py <episode.py> <out_dir>            # 전체 렌더 + mp4 + gif
  python3 build.py <episode.py> <out_dir> --only 0   # 프레임 하나만 (시안 확인용)
  python3 build.py <episode.py> <out_dir> --sheet    # 전체 렌더 후 프레임 비교 시트(sheet.png)도 생성
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))

import cartoon  # noqa: E402


def load_episode(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, name


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


PREVIEW = """<title>{title} 시안</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gowun+Dodum&display=swap">
<style>
:root{{--bg:#fbf8ef;--fg:#2a2522;--muted:#6f675f;--line:#e6dfcf;--accent:#e9c92e;
--font:"Gowun Dodum","Apple SD Gothic Neo","Malgun Gothic",sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#1d1b17;--fg:#f1ece2;--muted:#b3aa9c;--line:#3a352d;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#1d1b17;--fg:#f1ece2;--muted:#b3aa9c;--line:#3a352d;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:var(--font);font-size:16px;line-height:1.6;
padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:32px}}
main{{max-width:460px;margin:0 auto;display:grid;gap:20px}}
h1{{font-size:1.5rem;margin:0;text-wrap:balance}}
.meta{{color:var(--muted);font-size:.9rem;margin:4px 0 0}}
video{{width:100%;max-width:100%;aspect-ratio:9/16;border-radius:14px;border:1px solid var(--line);background:#fff;display:block}}
ul{{margin:0;padding-left:1.2em;display:grid;gap:6px}}
h2{{font-size:1.05rem;margin:0 0 8px;border-bottom:3px solid var(--accent);display:inline-block}}
</style>
<main>
<header><h1>{title}</h1><p class="meta">{version} · {layout} · 1080×1920 · {secs:.1f}초 루프</p></header>
<video src="data:video/mp4;base64,{b64}" autoplay muted loop playsinline controls></video>
<section><h2>컷 구성</h2><ul>{items}</ul></section>
</main>
"""


def write_preview(ep, out_dir, name, mp4):
    import base64
    import html
    title = " ".join(ep.TITLE) if isinstance(ep.TITLE, (list, tuple)) else ep.TITLE
    items = "".join(f"<li>{html.escape((tag + ' ') if tag else '')}{html.escape(cap)}</li>" for _, tag, cap in getattr(ep, "SLIDES", None) or ep.CELLS)
    n = getattr(ep, "N", cartoon.N)
    fps = getattr(ep, "FPS", cartoon.FPS)
    b64 = base64.b64encode(open(mp4, "rb").read()).decode()
    out = os.path.join(out_dir, "preview.html")
    with open(out, "w") as f:
        f.write(PREVIEW.format(title=html.escape(title), version=html.escape(getattr(ep, "VERSION", "시안")),
                               secs=n / fps, b64=b64, items=items,
                               layout="1x1 슬라이드" if getattr(ep, "LAYOUT", "grid") == "slide" else "2×2 4컷"))
    print(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("out_dir")
    ap.add_argument("--only", type=int)
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args()

    ep, name = load_episode(a.episode)
    fdir = os.path.join(a.out_dir, "frames")
    if a.only is None and os.path.isdir(fdir):
        shutil.rmtree(fdir)
    n = cartoon.render_episode(ep, a.out_dir, a.only)
    print(f"rendered {n} frame(s) -> {fdir}")
    if a.only is not None:
        print(os.path.join(fdir, f"f_{a.only:03d}.png"))
        return

    fps = getattr(ep, "FPS", cartoon.FPS)
    pat = os.path.join(fdir, "f_%03d.png")
    mp4 = os.path.join(a.out_dir, f"{name}.mp4")
    gif = os.path.join(a.out_dir, f"{name}.gif")
    ff("-framerate", str(fps), "-i", pat, "-vf", "fps=30,format=yuv420p",
       "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", mp4)
    ff("-framerate", str(fps), "-i", pat, "-vf",
       "scale=540:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=none",
       "-loop", "0", gif)
    print(mp4)
    print(gif)
    write_preview(ep, a.out_dir, name, mp4)
    if a.sheet:
        sheet = os.path.join(a.out_dir, "sheet.png")
        n_all = getattr(ep, "N", cartoon.N)
        picks = [0, n_all // 4 + 1, n_all // 2 + 3]
        ins = []
        for k in picks:
            ins += ["-i", os.path.join(fdir, f"f_{k:03d}.png")]
        ff(*ins, "-filter_complex",
           "[0]crop=1080:1150:0:540[a];[1]crop=1080:1150:0:540[b];[2]crop=1080:1150:0:540[c];[a][b][c]hstack=3,scale=2100:-1",
           sheet)
        print(sheet)


if __name__ == "__main__":
    main()
