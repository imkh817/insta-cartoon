# insta-cartoon

인스타용 낙서풍 2x2 4컷 루프 영상(MP4/GIF) 제작 저장소.

- 제작 스킬: `/create-video-copy` (직접 호출할 때만 동작) — `.claude/skills/create-video-copy/`
- 에피소드: `episodes/*.py` (기준작: `dating_1y_vs_3y.py`)

```bash
bash .claude/skills/create-video-copy/scripts/setup.sh
python3 .claude/skills/create-video-copy/scripts/build.py episodes/dating_1y_vs_3y.py out/dating --sheet
```
