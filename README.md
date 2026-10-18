# kearney-hotspot-11-bakery — 서울의 다음 베이커리 핫플

**사이트:** https://offthemenu.github.io/kearney-hotspot-11-bakery/  
**결론:** 3년 안에 뜰 베이커리 상권 1위는 **강동구 천호3동** (2위 강서구 등촌1동, 3위 강동구 성내2동)

## '뜬다'의 한 줄 정의
> 카페·베이커리 수요가 공급보다 빨리 늘고, 2030이 가볍게 자주 찾기 시작한 동네

지표 5개(검증 통과): 점포당 매출 증가 · 매출 모멘텀 · 2030 소비 비중 · 객단가 하락 · 여성 매출 비중(보조).
2022Q4~2024Q2 7개 시점 롤링 백테스트, 처음 보는 3개 시점에서 상위 20곳 적중률 20% (무작위 9.9%, 모멘텀만 15%).
사례: 중구 황학동 — 2023Q4·2024Q1 1위 → 2년 뒤 카페·베이커리 매출 +101~115%.

## 팀원 역할
| 이름 | 역할 |
|---|---|
| (이름) | 리드 · 지표 설계와 최종 의사결정 |
| (이름) | 데이터 수집·분석 (서울 열린데이터광장 API) |
| (이름) | 매장 콘셉트 · 발표 |
| Claude Code | 데이터 파이프라인, 백테스트, 사이트·모션그래픽 구현, 발표 대본 초안 |

## 파일
- `index.html` — 사이트 (상단에 30초 피치 영상)
- `assets/pitch.mp4` — 30초 피치 영상: 424개 행정동의 실제 점수로 만든 3D 데이터 시티 → 황학동 검증 → 천호3동
- `video/` — 영상 원본 (HyperFrames + Three.js 컴포지션, `npx hyperframes render` 로 재렌더). `scripts/video.template.html` + `scripts/video-dongs.json` 으로 `video/index.html` 생성
- `SCRIPT.md` — 3분 발표 대본
- `scripts/fetch.py` — 상권분석서비스(행정동) 데이터 수집 (`.env`의 `SEOUL_OPEN_API_KEY` 사용, 키는 커밋하지 않음)
- `scripts/panel.py`, `evaluate.py`, `composite.py` — 지표 패널, 지표별 백테스트, 종합점수 검증
- `scripts/analyze.py`, `backtest.py` — 1차 지표(탈락)와 그 백테스트 기록

재현: `python3 scripts/fetch.py && python3 scripts/composite.py`

## 데이터
서울 열린데이터광장 Open API, 서울시 상권분석서비스(행정동): 추정매출(VwsmAdstrdSelngW), 점포(VwsmAdstrdStorW), 길단위인구(VwsmAdstrdFlpopW), 상주인구(VwsmAdstrdRepopW), 상권변화지표(VwsmAdstrdIxQq). 2021Q1–2026Q2, 업종 제과점(CS100005)·커피-음료(CS100010). 외부 확인: 강동구 보도자료, 서울신문, KB Think.

## 사용한 프롬프트 (전문, 순서대로)
1. `https://jayden.airoasting.com/intro_kearney.html#mission This is our assignment. our subject is bakery. /superpowers:brainstorming`
2. `just ship it e2e`
3. `would you circle back once you have the bakery concept for approval? Let's keep this iteration under 15 mintues`
4. `replace 해방촌 it's already popping`
5. `would you further contextualize the reasoning behind suggesting the three spots`
6. `so thats your scoring criteria? Sales, bakery proportion, increase in foot traffic and seoul city designated change index? Whats this change index btw?`
7. `have we run enough backtest to retrieve a positive hit on this backtesting criteria? 과거에 뜬 상권 1곳에 내 지표를 적용했을 때 미리 잡아낼 수 있었는가`
8. `we need new testing metrics. 남영동 being the only provable point is unacceptable`
9. `we approve 천호3동. make sure you create a formidable html output that would stand against all scoring rubrics / Make sure we bake in the motiongraphics (30s max) / and a 3-minute script in Korean / Cap this entire operation under 15 minutes`
10. `could we have a motiongraphic content that's more than just a slideshow of our finished artifacts? I was thinking more like a pitch video with idk computer graphics and whatnot. is that not quite supported?`
11. `let's go with your recommendation`
