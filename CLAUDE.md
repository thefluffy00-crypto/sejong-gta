# 세종고GTA

조치원 세종고등학교를 위성지도, 현장 사진, 2026학년도 교사 건물 배치도로 옮긴 3D 캠퍼스 게임.
GitHub Pages로 배포: https://thefluffy00-crypto.github.io/sejong-gta/ (main 브랜치 루트, push하면 1~2분 뒤 반영)

## 구조

- `index.html` 한 파일에 HTML, CSS, JS(ES module)가 다 들어 있음. 빌드 단계 없음.
- Three.js r160을 importmap으로 jsDelivr에서 불러옴 (`three`, `three/addons/`). Sky, BufferGeometryUtils 사용.
- 모든 텍스처는 canvas로 직접 그림 (외부 이미지 없음). 글꼴은 Google Fonts (Noto Sans KR, Noto Serif KR, Black Han Sans, JetBrains Mono).

## 좌표계

- 위성사진을 12° 돌려 반듯하게 편 "캠퍼스 px" 좌표를 씀. `S=0.25` m/px, `X(px)=(px-430)*S`, `Z(py)=(py-480)*S`, 역변환은 `PX`, `PZ`.
- 월드: x 동쪽, z 남쪽, y 위. `ROT`(12°)는 실제 북쪽과의 차이로, 태양 방위와 화면 방위 표시에 보정으로 들어감.
- 건물 외곽은 `BD` 테이블(캠퍼스 px 사각형). A·B·C동 내부는 `LAYOUT` 블록 정의로 `ib()`가 만듦 (층 높이 `FH=3.8`, 복도 띠, lo/hi 방 슬롯, 계단·엘리베이터, 층 사이 구멍).

## 충돌과 바닥

- `boxes` `{x0,x1,z0,z1,top,bottom}`: `top`은 발 높이와, `bottom`은 눈 높이(pos.y)와 비교. `-99`나 없음은 항상 적용.
- `circles`는 기둥과 나무. `FLOORS`(층 바닥, holes 포함), `RAMPS`(계단), `RUBBLE`(무너진 잔해)로 `groundAt(x,z,feet)` 계산.
- 플레이어 `pos`는 눈 높이 기준 (`feet = pos.y - EYE`, `EYE=1.62`).

## 게임 시스템

- 모드: `MODE` = `'walk'`(일반, 비행·운석 없음) | `'meteor'`(F 비행, 클릭·G·H 운석). 시작 화면 `#start`, 일시정지 `#pause`.
- 3인칭 캐릭터: `buildHero()` 절차적 모델, `animHero()` 걷기·달리기·점프·비행·주먹 포즈. 카메라는 `placeCamera()`로 어깨 뒤 궤도를 돌고, `camCast()`로 벽·바닥·천장에 막힘.
- 자동차: `CARS` (`regCar`, `updateCars`, `enterCar`/`exitCar`, E키). 차는 원 두 개로 충돌 처리.
- 주먹: `punch()`, `punchHit()`.
- 운석과 파괴: `launch()`, `impact()`, `collapse()`, `restoreAll()`. 건물은 `DEST`에 등록되고, `assignDest()`가 장면 객체를 가장 가까운 건물에 붙임.
- 소리: Web Audio 합성 (`audio()`, `spot()`, 엔진·경적·충돌·발소리).
- 사진 맞춤 지점: P키로 카메라 위치, 방향, 썸네일을 저장. claude.ai 아티팩트에서는 공유 DB에, GitHub Pages에서는 localStorage에 저장되고, 메뉴의 "목록 복사"로 텍스트로 뽑을 수 있음.

## 사진으로 고치는 방법

사용자가 현장 사진을 주면 사진 속 기준점(골대, 센터서클, 건물 모서리 등)을 캠퍼스 px와 짝지어 카메라 위치, 방향, 화각을 최소제곱으로 역산하고, `__sj.cam(px,py,y,yaw,pitch,vfov)`로 같은 시점을 렌더해 나란히 비교한 뒤 고친다.
- 사진 1번(연문학사 2동 동쪽 3층 창문 → 북동쪽 운동장): 카메라 약 (381, 730.5), 높이 9.3m, 방위 43.8°, hfov 약 55°. B동 외벽 띠, 시계 박공, 트랙, 펜스, 은행나무, 아파트까지 반영함.

## 테스트

- Playwright + Chromium 헤드리스, swiftshader 사용 (`--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`). 로딩이 1분쯤 걸리고 프레임이 매우 느림 (dt가 0.05로 잘려서 물리가 느리게 진행됨).
- 로컬 테스트 때는 importmap 주소를 `node_modules/three`로 바꿔 끼운 사본을 띄움.
- 디버그 훅은 `window.__sj`: `play(mode)`, `mode`, `teleport(i)`, `setView(px,py,yaw,pitch,y)`, `cam(...)`, `keys`, `state()`, `meteor(big)`, `boom(px,py,big)`, `drive(i)`, `exit()`, `punch()`, `restore()`, `pause`/`resume`/`toTitle` 등.

## 원칙

- 실제 학교를 그대로 본뜬 맵이라 총, 로켓, 미사일 같은 실제 무기는 넣지 않음. 파괴는 운석 같은 자연재해 방식으로만 하고, 학교에 사람(NPC)을 넣어 공격하는 요소도 넣지 않음.
- UI 문구는 한국어. 다크 보라·금색 테마 (CSS 변수 `--purple`, `--gold`).
