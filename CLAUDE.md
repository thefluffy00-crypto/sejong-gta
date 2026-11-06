# 세종고GTA

조치원 세종고등학교를 위성지도, 현장 사진, 2026학년도 교사 건물 배치도로 옮긴 3D 캠퍼스 게임.
GitHub Pages로 배포: https://thefluffy00-crypto.github.io/sejong-gta/ (main 브랜치 루트, push하면 1~2분 뒤 반영)

## 구조

- `index.html` 한 파일에 HTML, CSS, JS(ES module)가 다 들어 있음. 빌드 단계 없음.
- 맨 위에 `<!doctype html>`과 `<meta charset="utf-8">`이 꼭 있어야 함. 없으면 quirks 모드로 뜨고, charset을 안 보내는 서버(`python -m http.server` 등)에서 한글이 깨짐.
- Three.js r160을 importmap으로 jsDelivr에서 불러옴 (`three`, `three/addons/`). Sky, BufferGeometryUtils, postprocessing(EffectComposer·RenderPass·GTAOPass·UnrealBloomPass·SMAAPass·OutputPass) 사용.
- 모든 텍스처는 canvas로 직접 그림 (외부 이미지 없음). 글꼴은 Google Fonts (Noto Sans KR, Noto Serif KR, Black Han Sans, JetBrains Mono).

## 좌표계

- 위성사진을 12° 돌려 반듯하게 편 "캠퍼스 px" 좌표를 씀. `S=0.25` m/px, `X(px)=(px-430)*S`, `Z(py)=(py-480)*S`, 역변환은 `PX`, `PZ`.
- 월드: x 동쪽, z 남쪽, y 위. `ROT`(12°)는 실제 북쪽과의 차이로, 태양 방위와 화면 방위 표시에 보정으로 들어감.
- 건물 외곽은 `BD` 테이블(캠퍼스 px 사각형). A·B·C동 내부는 `LAYOUT` 블록 정의로 `ib()`가 만듦 (층 높이 `FH=3.8`, 복도 띠, lo/hi 방 슬롯, 계단·엘리베이터, 층 사이 구멍).

## 충돌과 바닥

- `boxes` `{x0,x1,z0,z1,top,bottom}`: `top`은 발 높이와, `bottom`은 눈 높이(pos.y)와 비교. `-99`나 없음은 항상 적용.
- `circles`는 기둥과 나무. `FLOORS`(층 바닥, holes 포함), `RAMPS`(계단), `RUBBLE`(무너진 잔해)로 `groundAt(x,z,feet)` 계산.
- 플레이어 `pos`는 눈 높이 기준 (`feet = pos.y - EYE`, `EYE=1.62`).

## 캐릭터

기본은 `buildHero()`의 절차적 학생(교복·넥타이·백팩, 12관절). 외부 리깅 glTF/GLB로 갈아끼울 수 있음.

- `HERO = { url, anim, height, faceFix, clips }`가 설정 지점. `url`이 비어 있으면 절차적 학생을 씀. `localStorage['sejong3d.hero']`/`['sejong3d.heroAnim']`가 있으면 그걸 우선. 런타임 교체는 `__sj.hero3d(url, animUrl)`, 되돌리기는 `__sj.hero3d('','')`, 상태는 `__sj.gh()` (찾은 뼈·실제로 쓰는 클립·모델에 들어 있는 전체 클립 목록).
- **별도 애니메이션 파일**: 캐릭터 팩과 애니메이션 라이브러리는 보통 따로 배포됨(예: Quaternius Universal Base Characters + Universal Animation Library). `HERO.anim`에 클립만 든 두 번째 glTF를 주면 합쳐서 씀. 같은 리그면 트랙 이름이 맞아서 Blender로 합칠 필요 없음. `clipFit()`이 트랙 이름이 실제 노드와 30% 미만으로 맞으면 그 클립을 버리고 경고함 — 리그가 다르면 조용히 안 움직이는 대신 콘솔에 뜸.
- 파일이 없거나, SkinnedMesh가 없거나, 뼈를 6개 미만으로 찾으면 **조용히 절차적 학생으로 폴백**함. 게임은 안 죽음.
- **스케일**: 모델 bbox 높이를 재서 `HERO.height`(1.75m)에 맞춤. `Box3.setFromObject`는 matrixWorld를 보는데 로드 직후엔 갱신이 안 돼 있어서 **`updateMatrixWorld(true)`를 먼저 불러야 함**. 안 그러면 노드 스케일이 0.01인 리그가 100배 크게 나옴(실제로 밟았던 버그).
- **뼈 매핑**: `BONE_KEYS`에 믹사모 이름 우선으로 후보를 나열하고 `normBone()`이 `mixamorig:` 접두사와 기호를 털어낸 뒤 정확 일치 → 접미사 일치 순으로 찾음. `LeftUpLeg`(허벅지)과 `LeftLeg`(정강이)를 헷갈리지 않게 순서가 중요함.
- **리타게팅**: 리그마다 뼈 로컬축이 달라서 `rotation.x`를 그대로 쓰면 안 됨. `captureAxes()`가 **레스트 포즈에서 각 뼈의 부모 프레임 기준으로 캐릭터의 X/Y/Z축이 어느 방향인지** 미리 구해 두고, `swing()`이 그 축으로 `premultiply`함. 덕분에 기존 포즈 값(`P.thR`, `P.sxR` …)이 어떤 스켈레톤에서도 같은 동작이 됨.
- **애니메이션 레이어**: 이동(idle/walk/run)은 모델 자체 클립을 `AnimationMixer`로 돌리고 `timeScale`을 실제 속도에 맞춰 발 미끄러짐을 줄임. 점프·비행·주먹·킥·운석 소환은 어떤 기성 팩에도 클립이 없으므로 **기존 손수 만든 포즈를 뼈에 입혀서** 클립 위에 크로스페이드(`aw`)로 얹음. 액션이 세질수록 클립 가중치를 낮춰(`lw`) 다리가 이중으로 움직이지 않게 함.
- 모델은 `H.body` 밑에 붙어서 기존 위치·`face` 회전·기울기·블롭 그림자를 그대로 물려받음. 절차적 몸은 `H.pelvis.visible=false`로만 숨김.
- **지금 들어 있는 모델**: `models/student.gltf` + `Superhero_Male_FullBody.bin` (732KB). Quaternius Universal Base Characters의 **무료 Standard 티어** — CC0(`models/LICENSE-Quaternius.txt`). 주의할 점 두 가지:
  - 무료 티어에는 **Superhero 남/녀만** 들어 있음. 웹페이지가 광고하는 Regular·Teen 체형은 SOURCE(Patreon) 버전에만 있음. 그래서 지금 캐릭터는 고등학생이 아니라 근육질 성인 체형임.
  - 이 팩 자체에는 **애니메이션이 0개**. 지금은 `HERO.anim`으로 Universal Animation Library를 붙여 씀. 클립이 아예 없으면 `GH.hasClips`가 false가 되고 기존 손수 만든 애니메이션이 전체를 구동함(폴백 경로, 동작 확인됨).
  - 원본 텍스처(PNG 7장, 약 17MB)는 저장소에 넣기엔 너무 커서 glTF에서 참조를 지웠음. 교복은 canvas로 그려 입힐 예정.
- **본 이름이 언리얼식**: `pelvis`, `spine_01~03`, `clavicle_l`, `upperarm_l`, `lowerarm_l`, `thigh_l`, `calf_l`, `foot_l`. 믹사모식(`mixamorigLeftArm` …)과 둘 다 `BONE_KEYS`에 들어 있음.
- **T-포즈**: 팔을 벌린 채로 배포되는데 기존 포즈들은 팔이 내려간 자세를 전제로 함. `relaxTPose()`가 로드 시 한 번 팔을 내리고 그 상태를 레스트로 삼음. 상완만 75° 돌리면 삼각근 스키닝이 늘어나 뾰족한 조각이 보이므로 **쇄골이 30%를 나눠 받음**.
- **축은 반드시 캐릭터 기준으로**: `relToRoot()`가 월드가 아니라 `GH.root`를 거쳐 축을 구함. 월드 기준으로 캡처하면 `face` 회전만큼 축이 틀어져서 **앞으로 차는 킥이 옆으로 나감**(실제로 밟았던 버그). 검증은 서로 다른 두 방향에서 같은 값이 나오는지로 함.
- **애니메이션**: `models/animations.glb` — Quaternius Universal Animation Library(CC0)에서 `Idle_Loop`, `Walk_Loop`, `Jog_Fwd_Loop`, `Jump_Loop` 4개만 추려낸 것. 원본 `UAL1_Standard.glb`는 43개 클립에 7.27MB라 웹에 그대로 올리기엔 큼. `tools/slim_glb.py`가 필요한 클립의 accessor만 남기고 버퍼를 다시 만들어 **0.74MB**로 줄임. 루트모션 없는 쪽(`_RM`이 안 붙은 파일)을 써야 함 — 위치는 게임이 직접 움직이므로.
- **리그 호환**: 베이스 캐릭터와 애니메이션 라이브러리의 본 이름이 **100% 일치**함(채널 65개 전부). 그래서 `HERO.anim`으로 그냥 합쳐짐.
- **클립 고르기**: 라이브러리에 변형이 많아서 단순 `includes` 매칭이면 `Idle_Loop` 대신 `Crouch_Idle_Loop`이, `Walk_Loop` 대신 `Walk_Formal_Loop`이 걸림. `pickClip()`이 점수제로 고름 — 앞쪽 힌트 우선, 그다음 힌트로 시작하는 이름, 그다음 짧은 이름.

## 교복 입히기

베이스 메시는 알몸이라 옷을 칠해야 함. `bakeUniform()`이 **삼각형을 UV 공간에 래스터화하면서 각 텍셀에 대응하는 3D 좌표를 보간해, 그 위치로 색을 정함**(`uniformAt(x,y,z,H)`). 모델별 UV 레이아웃을 몰라도 되고 어떤 리깅 휴머노이드에도 통함.

- **사각형으로 칠하면 안 되는 이유**: UV 섬들의 바운딩 박스가 서로 겹침(머리 섬과 몸통 섬이 `u 0.236~0.280`에서 겹침). 사각형을 칠하면 옆 섬에 번짐. `tools/`에 UV를 그려 보는 스크립트는 없지만, 필요하면 `TEXCOORD_0`와 인덱스를 읽어 선으로 그리면 됨.
- **기준점**(1.81m 기준 모델 공간, `t()`가 실제 키로 환산): 신발 <0.12 · 바지 <1.06 · 벨트 ~1.08 · 블레이저 1.10~1.50 · 칼라 1.50~1.60 · 머리 >1.60. 팔은 높이가 아니라 `|x|`로 판정 — T-포즈 기준 소매 <0.60, 커프스 ~0.63, 손 >0.655.
- **얼굴도 같은 몸통 메시**에 있으므로 눈·눈썹·입을 좌표로 찍음. 팩에 들어 있는 별도 Eyes/Eyebrows 평면은 텍스처가 없으면 얼굴에 **검은 띠**로 보여서 `visible=false`로 숨김.
- 섬 경계에서 bilinear 보간이 빈 공간을 물지 않도록 커버된 픽셀을 바깥으로 4번 번지게 함(dilate).
- `CanvasTexture`는 기본 `flipY=true`인데 glTF UV는 좌상단 원점이므로 **`tex.flipY=false` 필수**.
- 끄려면 `HERO.uniform=false` 또는 `__sj.dress(false)`.

- **에셋 출처**: Quaternius `Universal Base Characters` + `Universal Animation Library`(둘 다 CC0). itch.io에서 받음. 믹사모는 FBX/DAE만 내보내서 Blender 변환이 필요하고 재배포가 회색지대.
- **에셋 라이선스**: 공개 저장소이므로 CC0만 커밋할 것. 믹사모 에셋은 게임에 쓰는 건 되지만 재배포는 회색지대라 저장소에 넣지 말 것. 테스트는 three.js 저장소의 `Xbot.glb`를 jsDelivr로 불러 확인했음(테스트 전용).
- 어떤 CC0 팩에도 한국 교복은 없음. 받은 모델 텍스처를 지금처럼 canvas로 다시 그려 입히는 게 현실적.

## 그래픽 (IBL과 후처리)

- **환경맵**: `bakeEnv()`가 `Sky`를 복제한 `envScene`을 `PMREMGenerator.fromScene(envScene, 0, 1, 20000)`으로 구워 `scene.environment`에 넣음. far를 2만까지 열어야 9000 스케일 하늘이 안 잘림. 시간대를 바꿀 때마다 다시 구움.
- **envI 함정**: Sky는 HDR이라 값이 매우 큼. `envMapIntensity`를 0.7쯤 주면 반구 전체가 ambient로 들어와 태양과 그림자를 다 덮어버리고 화면이 뿌옇게 됨. 프리셋의 `envI`는 낮 .18 / 노을 .12 / 밤 .08 수준으로 유지할 것. `ALLMATS`(빌드 후 `collectMats()`가 모음)에 일괄 적용.
- **후처리**: `GFX` 0 낮음(composer 없이 직접 렌더) · 1 중간(블룸+SMAA) · 2 높음(+GTAO). `buildComposer()`가 매번 새로 만들고, `setGfx()`가 localStorage(`sejong3d.gfx`)에 저장. 터치 기기는 0, 데스크톱은 **1이 기본**.
- **비용 측정**(1024×768, vsync 60 상한): 낮음 60 · 중간 58 · 높음 **23**. 높음에서 블룸만 끄면 25, **GTAO만 끄면 50** — 비싼 건 전적으로 GTAO임. 깊이·법선 G버퍼를 위해 매 프레임 캠퍼스 전체를 다시 그리기 때문. 그래서 기본값은 중간이고 높음은 선택임. 더 줄이려면 AO를 절반 해상도로 렌더하면 됨(`gtaoPass.setSize`를 composer와 따로 호출).
- fps를 잴 땐 브라우저 페인이 **보이는 상태**여야 함. 숨겨져 있으면 백그라운드 페이지로 throttle돼서 절대값이 의미 없음. 반대로 둘 다 vsync 60에 걸려 있으면 차이가 안 보이므로, 무거운 설정끼리 비교할 것.
- **톤매핑**: three는 렌더타깃에 그릴 때 톤매핑을 적용하지 않음(`currentRenderTarget === null`일 때만). 그래서 composer 경로에서는 머티리얼이 선형 HDR을 그대로 쓰고 맨 끝 `OutputPass`가 ACES + sRGB를 적용함. 이중 적용 아님.
- **블룸 임계값**: 블룸도 톤매핑 전 HDR 값을 보기 때문에 threshold를 0.95로 두면 하늘 전체가 걸려 화면에 뿌연 막이 낌. 1.9 정도로 둘 것.
- **GTAO**: 깊이·법선을 override material로 다시 그리기 때문에 알파컷 펜스나 wireframe 골네트가 통짜 벽으로 잡힘. `collectAO()`가 그런 메시(+하늘)를 `AO_HIDE`에 모아 두고, `gtaoPass.render`를 감싸서 그 패스 동안만 `visible=false`로 내림. AO는 접촉 효과라 실외 원경에선 거의 안 보이고 복도·계단 같은 실내에서 확실히 보임 (radius 2m).

## 게임 시스템

- 모드: `MODE` = `'walk'`(일반, 비행·운석 없음) | `'meteor'`(F 비행, 클릭·G·H 운석). 시작 화면 `#start`, 일시정지 `#pause`.
- **UI는 최소로 유지할 것** (사용자 요청). 게임 중 화면에 있는 건 **미니맵뿐**. 위치·방위·속도·점프 높이·모드 표시·키 안내 띠는 전부 뺐음. 터치 기기에서만 오른쪽 위 `#tr`(메뉴·운석)과 조이스틱·버튼이 뜸.
- 시작 화면과 일시정지는 같은 세로 메뉴를 씀. `menuNav(메뉴셀렉터, 패널셀렉터, onPick)`이 위아래 키·마우스·클릭을 처리하고, `.mi[aria-current="true"]`가 노란 강조임. 항목은 `data-act`(시작 화면) / `data-pact`(일시정지).
- `openPanel(M,'keys'|'gfx')`가 메뉴 아래에 패널을 펼침. **설정은 그래픽뿐** — 시간대(낮/노을/밤) 선택 UI는 뺐고 기본값은 `day`. 밤이 필요하면 `__sj.applyPreset('night')`.
- 시작 화면 배경은 `attractCam()`의 저공 궤도(R=152, 높이 42). 너무 높이·멀리 두면 안개에 묻혀 어두워 보임.
- 3인칭 캐릭터: `buildHero()` 절차적 모델, `animHero()` 걷기·달리기·점프·비행·주먹 포즈. 카메라는 `placeCamera()`로 어깨 뒤 궤도를 돌고, `camCast()`로 벽·바닥·천장에 막힘.
- 자동차: `CARS` (`regCar`, `updateCars`, `enterCar`/`exitCar`, E키). 차는 원 두 개로 충돌 처리.
- 주먹: `punch()`, `punchHit()`.
- 운석과 파괴: `launch()`, `impact()`, `collapse()`, `restoreAll()`. 건물은 `DEST`에 등록되고, `assignDest()`가 장면 객체를 가장 가까운 건물에 붙임.
- 축구: 운동장(`FIELD`)에 공 하나. 걸어서 밀면 드리블, 공 옆(1.9m 안)에서 클릭하면 슛(`kick()` → 애니메이션 중간 `kickHit()`에서 임펄스, Shift면 강슛, 시선 pitch만큼 띄움). 골대 기둥은 원래 `circles`에 있어서 그대로 맞고 튐. 골라인(`FIELD.z0+3`, `FIELD.z1-3`)을 기둥 사이·크로스바(2.44m) 아래로 통과하면 `scoreGoal()` → 1.4초 뒤 센터서클로 리셋. `B`키로 공을 발 앞에 가져옴. NPC는 없음.
- 부서지는 사물(`SMASH`): 나무·관목·가로등·피크닉 테이블 **370개**가 등록돼 있음. 차로 들이받으면 쓰러지고 파편이 튐.
  - 등록은 `smashMark()`로 인스턴스/circles 인덱스를 찍고 `smashReg()`로 범위를 저장하는 식. 나무 생성 함수(`pine`/`broad`/`column`/`ginkgo`/`shrub`) 안에서 직접 부르므로 `scatter()` 같은 간접 호출도 전부 잡힘.
  - `smashProp(sp,dirx,dirz,power)`: circles를 떼고, 밑동을 축으로 인스턴스와 개별 메시를 함께 기울이고, 파편·소리. 회전축은 `(dz,0,-dx)` — 부호를 뒤집으면 나무가 **차 쪽으로** 쓰러짐.
  - `carSmash(c)`가 `carHits(c)` **앞에** 호출됨. 순서가 바뀌면 이미 쓰러진 물체에 차가 튕김. 종류별 `tough`(필요 속도)와 `drag`(감속)로 관목은 스치고 지나가고 가로등은 확 느려지게 함.
  - 되돌리기는 기존 `SAVED`(인스턴스 행렬)와 `FX.rmCircles`에 얹었고, 개별 메시만 `SMASH_MOVED`로 따로 저장함. `restoreAll()`에서 전부 복구됨.
  - 주먹으로는 `tough<=3`인 것(관목)만 부서짐.
  - `spawnDebris(p,n,spd,up,big,opt)`의 `opt`로 `smin/smax/spread/cols`를 줄 수 있음. 안 주면 기존 건물 잔해 크기라 가로등 파편이 1m 덩어리로 나옴.
  - 디버그: `__sj.smash()`, `__sj.smashNear(px,py,r)`, `__sj.putCar(i,px,py,aRad,v)`.
  - **주의**: `updateCars`의 `moving` 판정은 `c.v`를 보지 않음(`drv || air || vx+vz>.02 || wob`). 주차된 차에 `c.v`만 넣어도 안 움직이므로, 테스트할 땐 `__sj.drive(i)`로 운전 상태를 만들 것.
- 소리: Web Audio 합성 (`audio()`, `spot()`, 엔진·경적·충돌·발소리, 공 바운스·골).
- 사진 맞춤 지점: P키로 카메라 위치, 방향, 썸네일을 저장. claude.ai 아티팩트에서는 공유 DB에, GitHub Pages에서는 localStorage에 저장되고, 메뉴의 "목록 복사"로 텍스트로 뽑을 수 있음.

## 사진으로 고치는 방법

사용자가 현장 사진을 주면 사진 속 기준점(골대, 센터서클, 건물 모서리 등)을 캠퍼스 px와 짝지어 카메라 위치, 방향, 화각을 최소제곱으로 역산하고, `__sj.cam(px,py,y,yaw,pitch,vfov)`로 같은 시점을 렌더해 나란히 비교한 뒤 고친다.
- 사진 1번(연문학사 2동 동쪽 3층 창문 → 북동쪽 운동장): 카메라 약 (381, 730.5), 높이 9.3m, 방위 43.8°, hfov 약 55°. B동 외벽 띠, 시계 박공, 트랙, 펜스, 은행나무, 아파트까지 반영함.

## 되돌린 작업: 2026-11 현장 사진 24장 (중요)

사용자가 교내 사진 24장(정원 표석, 운동장 앞 길, 트랙, 웅비관 주차장, 연문학사 2동, 검무관, 농구장, 관객석, 급식실, 신발장 등)을 주면서 “외부가 현실과 안 맞는다”고 해서, 볼스톱 네트·야외무대·관객석·주차 캐노피·자전거 보관소·농구 골대·표석·신발장·현관 간판을 넣고 검무관을 돌렸음(`fcdf51d`, `69a78e2`). **사용자가 보고 “맞는 게 거의 없다”고 해서 둘 다 revert 했음.**

무엇이 잘못됐는지:

- 사진에 찍힌 **기준점을 캠퍼스 px와 짝지어 역산하지 않고**, “이 사진은 아마 여기겠지” 하고 눈대중으로 좌표를 넣었음. 사진 1장당 추정이 한 번씩 들어가니 24장이 전부 어긋났음.
- 사진에 뭐가 보이는지(네트 펜스, 캐노피, 골대)는 맞았지만 **어디인지가 틀렸음**. 물건을 만드는 건 쉽고 위치를 맞추는 게 전부인 작업임.
- 애초에 `BD` 테이블(건물 외곽) 자체가 위성사진과 어긋나 있을 가능성도 아직 안 지웠음. 그게 틀려 있으면 그 위에 뭘 올려도 다 어긋남.

다음에 할 때:

1. 먼저 `docs/campus-plan.svg`(현황 평면도 생성 스크립트는 세션 스크래치에 있었음 — 필요하면 다시 그릴 것)처럼 **격자 붙은 평면도를 뽑아 사용자에게 칸 번호를 받을 것.** 사진마다 “어느 칸에서 어느 쪽을 보고 찍었는지”를 먼저 확정한 다음에 코드를 건드릴 것.
2. 사용자가 건물 배치부터 틀렸다고 하면 `BD`부터 다시 잡을 것.
3. 내가 브라우저에서 “구조물이 존재한다”를 확인한 건 검증이 아님. **사진과 같은 시점을 렌더해서 나란히 비교**해야 검증임.

건질 만한 기술 메모(코드는 되돌렸지만 다시 쓸 때 유효함):

- 열린 실린더로 볼트 지붕을 만들 때 `thetaStart`는 마루(θ=90°)를 가운데 둬야 함. `CylinderGeometry(...,0,Math.PI)` + `rotateZ(π/2)`면 y=sinθ라 아치가 됨. 시작각을 옮기면 **V자**가 나옴. 축을 z로 돌릴 땐 `rotateX(π/2)` + `thetaStart=π/2`.
- `Object.assign(mesh,{position:new V3(...)})`는 three에서 에러남(`position`은 읽기 전용). `mesh.position.set(...)`을 쓸 것.
- 선을 따라 세우는 벽은 평면(`rotation.y=a+π/2`)과 그 뒤 흙더미 박스의 회전을 똑같이 줘야 함. 박스만 `rotation.y=a`로 두면 벽과 직각으로 누움.
- `facade()`가 돌려주는 머티리얼의 맵은 ClampToEdge라 `repeat`가 안 먹음. 타일링하려면 `wrapS/wrapT=RepeatWrapping`을 직접 켤 것.
- 로컬 `python -m http.server`는 304를 돌려줌. 고친 게 안 보이면 `?v=N`을 붙일 것. GitHub Pages도 index.html을 10분쯤 캐시함 — 사용자가 “안 바뀌었다”고 하면 캐시부터 확인할 것.

## 테스트

- Playwright + Chromium 헤드리스, swiftshader 사용 (`--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`). 로딩이 1분쯤 걸리고 프레임이 매우 느림 (dt가 0.05로 잘려서 물리가 느리게 진행됨).
- 로컬 테스트 때는 importmap 주소를 `node_modules/three`로 바꿔 끼운 사본을 띄움.
- 디버그 훅은 `window.__sj`: `play(mode)`, `mode`, `teleport(i)`, `setView(px,py,yaw,pitch,y)`, `cam(...)`, `keys`, `state()`, `meteor(big)`, `boom(px,py,big)`, `drive(i)`, `exit()`, `punch()`, `restore()`, `pause`/`resume`/`toTitle` 등.
- 그래픽·축구 쪽 훅: `THREE`, `scene`, `camera`, `renderer`, `composer`, `gtao`, `gfx(0|1|2)`, `env(i)`, `noEnv()`, `reEnv()`, `exp(e)`, `hemi(i)`, `sunI(i)`, `ball()`, `kick()`, `putBall(px,py)`, `fps()`. 조명을 고칠 땐 `gfx(0)`으로 후처리를 끄고 `noEnv()`/`reEnv()`로 IBL을 껐다 켜 가며 원인을 가를 것.
- 헤드리스에서 rAF가 throttle되면 dt가 0.05로 잘려 플레이어가 거의 안 움직임. 걸어서 하는 테스트는 실패로 오해하기 쉬우니, 대상 바로 옆에 놓고 한 프레임 안에 끝나는 식으로 확인할 것.

## 원칙

- 실제 학교를 그대로 본뜬 맵이라 총, 로켓, 미사일 같은 실제 무기는 넣지 않음. 파괴는 운석 같은 자연재해 방식으로만 하고, 학교에 사람(NPC)을 넣어 공격하는 요소도 넣지 않음.
- UI 문구는 한국어. 다크 보라·금색 테마 (CSS 변수 `--purple`, `--gold`).
