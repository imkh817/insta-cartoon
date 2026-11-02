#!/usr/bin/env bash
# 렌더링에 필요한 도구(ffmpeg, Pillow, 나눔 폰트)가 없으면 설치한다.
set -e
need=()
command -v ffmpeg >/dev/null || need+=(ffmpeg)
python3 -c "import PIL" 2>/dev/null || need+=(python3-pil)
[ -f /usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf ] || need+=(fonts-nanum)
if [ ${#need[@]} -gt 0 ]; then
  echo "installing: ${need[*]}"
  sudo -n apt-get install -y "${need[@]}" >/dev/null 2>&1 || {
    sudo -n apt-get update >/dev/null 2>&1 && sudo -n apt-get install -y "${need[@]}" >/dev/null 2>&1
  }
fi
echo "ready"
