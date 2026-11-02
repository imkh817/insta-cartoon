---
name: create-video-copy
description: 인스타용 낙서풍 2x2 4컷 루프 영상(움짤)을 주제 → 기획·자막 → 제작 3단계로, 단계마다 사용자 검수를 받으며 만든다. 사용자가 /create-video-copy 로 직접 호출할 때만 사용.
disable-model-invocation: true
argument-hint: "[주제 또는 레퍼런스 설명 (선택)]"
---

# create-video-copy

손그림 느낌의 2x2 4컷 세로 루프 영상(MP4 + GIF)을 만든다.
기준작: `episodes/dating_1y_vs_3y.py` ("연애 1년차 vs 3년차 데이트 차이"). 사용자가 "완전 좋다"고 승인한 퀄리티이므로 **새 작업은 항상 이 수준 이상**이어야 한다.

## 진행 원칙

- 사용자와 **회의하듯** 진행한다. 3단계를 나눠서, **단계마다 검수(OK)를 받은 뒤에만** 다음 단계로 넘어간다.
- 대화는 한국어로 한다. 결정이 필요한 것은 선택지 2~4개와 추천안으로 묻는다.
- `$ARGUMENTS`로 주제나 레퍼런스가 주어지면 1단계에서 그것부터 다룬다.
- 레퍼런스 영상이 첨부되면 먼저 분석한다. ffmpeg로 1fps 컨택트 시트와 확대 크롭을 만들어 보고, 규격·구성·움직임·톤을 표로 정리한다.

## 1단계: 주제

- "공감되는 특징 N가지", "N년차 vs M년차", "~할 때 특징"처럼 **표정으로 웃길 수 있는** 커플/일상 공감 소재를 3~4개 제안한다.
- 각 후보마다 제목 안과 4컷 예시를 붙인다.
- 사용자가 고르거나 수정하면 2단계로 간다.

## 2단계: 기획 + 자막

아래 표 형식으로 초안을 제시하고 검수를 받는다.

- 제목: 노란 상자에 1~2줄. `치@명적`처럼 한 단어를 비트는 것은 선택 사항이다.
- 4컷마다 다음을 정한다.
  - 캡션: 컷 아래 한 줄. 필요하면 "1년차"처럼 색 태그를 붙인다.
  - 장면: 누가, 어떤 표정과 포즈인지.
  - 말풍선: 짧게, 3~6자.
  - 루프 움직임: 2~3포즈 교체.
- 비교형 주제는 **위 줄 = A, 아래 줄 = B, 같은 열 = 같은 소재**로 배치해 위아래로 비교되게 한다.
- 한 컷 = 캐릭터 1~2명 + 소품 0~1개. 상황 설명은 글이 아니라 **표정과 몸짓**으로 한다.

## 3단계: 제작

1. 준비: `bash .claude/skills/create-video-copy/scripts/setup.sh` (ffmpeg, Pillow, 나눔 폰트)
2. 에피소드 파일 작성: `episodes/<slug>.py`. 기준작을 복사해 시작한다. 형식은 아래 "에피소드 파일"을 참고한다.
3. 시안 확인: `python3 .claude/skills/create-video-copy/scripts/build.py episodes/<slug>.py <scratchpad>/<slug> --only 0`
   - 결과 PNG를 직접 Read로 보고 겹침, 잘림, 어색한 포즈를 고친다. 직접 1~2회 다듬은 뒤 사용자에게 보여준다.
4. 전체 빌드: `python3 .claude/skills/create-video-copy/scripts/build.py episodes/<slug>.py <scratchpad>/<slug> --sheet`
   - `<slug>.mp4`, `<slug>.gif`, `preview.html`, `sheet.png`(프레임 3장 비교)가 만들어진다.
   - sheet.png로 움직임이 실제로 바뀌는지 확인한다.
5. 전달: 먼저 SendUserFile로 mp4와 gif를 보낸다. 실패하면 `preview.html`을 Artifact로 게시한다. 같은 영상의 수정본은 같은 file_path로 재게시해 링크를 유지한다.
6. 검수 요청: 그림체와 표정, 문구, 움직임 속도. 수정을 반영해 같은 링크로 재게시한다.
7. 승인되면 에피소드 파일을 커밋한다. 산출물(`out/`, mp4, gif)은 커밋하지 않는다. 사용자가 원하면 예외로 한다.

## 스타일 규칙 (레퍼런스 비교로 확정된 것)

해야 할 것:
- **흰 바탕에 캐릭터만** 둔다. 컷 테두리, 배경 박스, 배경색은 쓰지 않는다. 예외적으로 영화관 같은 분위기도 소품 1개로 처리한다.
- **2x2 4컷**, 컷 하나는 470x450이다. 캐릭터 머리 반지름은 주인공 80~105, 조연 50~60으로 컷을 꽉 채운다.
- **표정과 포즈가 웃음 포인트**다. 반짝눈, 눈물, 하트눈, 반쯤 감은 눈, 눈곱, 하품, 침, 콧방울, 땀, 떨림 표시, 볼터치 빗금을 활용한다.
- **펜 선**: 굵기가 들쭉날쭉한 도장 브러시(`Pen.stroke`)를 쓴다. 매 프레임 boil(t % 3)로 미세하게 떨린다.
- **움직임**: 컷마다 포즈 2개 이상을 교체한다(고개 갸웃, 덜덜, 긁기, 하품 열고 닫기, 하트·반짝이·Zzz 위치 변화). 주기는 N을 나누어떨어지게 맞춘다(N=96이면 6, 12, 24).
- **색**: 진한 대비를 쓴다. 핫핑크 리본, 갈색 곰, 노란 반짝이, 빨강 입.
- **글씨**: 얇은 나눔바른고딕(일반 굵기)을 쓴다. 제목 54, 캡션 30, 말풍선 28~30.

하지 말 것 (v1에서 "별로"라는 피드백을 받은 원인):
- 색 배경 박스 8칸을 빽빽하게 배치한 인포그래픽 느낌
- 작은 캐릭터 + 식탁, 폰, 소파, 간판 같은 소품 과다
- 팔다리 없는 눈사람 캐릭터, 모든 컷이 정면에 같은 자세
- 굵기가 일정한 매끈한 벡터 선, 파스텔 톤, 두꺼운 둥근 고딕

## 에피소드 파일

```python
import math
from cartoon import *          # Pen, bunny, bear, popcorn, 색 상수 등

TITLE = ["첫 줄", "둘째 줄"]   # 1~2줄
VERSION = "시안 v1"            # 미리보기 페이지 표시용
FPS = 10
N = 96                          # 프레임 수 (9.6초 루프)

def cut_a(p, t):                # 로컬 좌표 (0..470, 0..450), t = 프레임 번호
    ph = (t // 4) % 2           # 포즈 교체
    bunny(p, 195, 225, 100, -7 if ph else 7, "sparkle", "kiss", ("blush",),
          body=(195, 375, 72, 62))
    p.bubble(90, 80, "어때?", 30, (140, 140))

CELLS = [(cut_a, "태그", "캡션"), ...]   # 정확히 4개: 좌상, 우상, 좌하, 우하
TAG_COLORS = {"태그": (235, 60, 120)}
```

### 엔진 API 요약 (`engine/cartoon.py`)

- 캐릭터
  - `bunny(p, hx, hy, hr, tilt, eyes, mouth, extras, body=(x,y,rx,ry), arms=[((어깨),(손))], arms_back=..., ribbon=True, ears="up"|"messy", body_fill=BUNNY|HOODIE)`: 여친 토끼
  - `bear(p, hx, hy, hr, tilt, eyes, mouth, extras, body=..., arms=...)`: 남친 곰
- 표정 값
  - `eyes`: `sparkle` `teary` `heart` `dot` `down` `happy` `closed` `half`
  - `mouth`: `kiss` `smile` `grin` `flat` `wobbly` `yawn` `o` `drool`
  - `extras`: `blush` `blush+`(빗금) `boogers` `sweat`
- 펜(`p`)
  - 도형: `blob(cx,cy,rx,ry,fill,w,ang)`, `capsule(p0,p1,r0,r1,fill)`(팔다리), `shape(pts,fill,w)`, `line(pts,w)`, `arc(...)`
  - 장식: `heart`, `sparkle`, `bubble(x,y,글,크기,꼬리끝)`, `text(x,y,글,크기,색,anchor)`
- 소품: `popcorn(p,x,y,s,tipped)`
- 그리는 순서가 곧 앞뒤 관계다. 뒤에 있는 것을 먼저 그린다. 껴안는 팔처럼 앞으로 나와야 하는 부위는 `capsule`로 마지막에 덧그린다.
- 새 캐릭터, 표정, 소품이 필요하면 `engine/cartoon.py`에 **추가**한다. 기존 함수의 기본 동작은 바꾸지 않는다. 기준작이 똑같이 렌더링돼야 하므로, 엔진을 고친 뒤 기준작 프레임 0을 렌더링해 확인한다.
