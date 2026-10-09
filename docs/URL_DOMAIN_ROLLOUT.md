# 맛집·레시피 고정 URL 및 도메인 이관 설계 (2026-10-10)

## 작업 전 확인
- main 공개 식당 `data/restaurants.json`: **0건**; 승인 레시피 `data/recipes.json`: **0건**.
- 기존 `index.html?restaurant=<public_id>`, `recipes.html?recipe=<public_id>`의 화면/기능을 보존해야 함.
- cafe UI 확장 PR #5 별도 검토 중. 이 브랜치는 해당 PR을 병합하거나 변경하지 않음.
- 공개 사이트/비공개 source 데이터를 분리하고, 출처 URL 내부 매핑과 수집기는 Public에 넣지 않는다.

## 기본 계약
- 도메인 후보는 `food.evococoons.com` / `food.prince-in-wonderworld.com`; 모두 **미확정**, 이 PR에서 DNS/Pages Custom Domain/CNAME 미설정.
- `site.config.json`: `public_origin: null`.
- `data/url-routes.json`: 승인된 `restaurant_id`/ `recipe_id` → 사람이 읽는 경로 (stable explicit slug registry).
- 후보 경로: `restaurants/{region}/{slug}/`, `recipes/{food-group}/{slug}/`. 슬러그는 영문 소문자 + 숫자 + 하이픈.
- `scripts/build_public_routes.py`: Public validator에 이미 통과한 레코드 + 정확한 매핑이 있는 때에만 해당 경로 `index.html` 생성. 미승인/빠진 slug/중복 경로/빈 정보는 실패로 처리.
- 현재 데이터가 0건이므로 **아직 실제 공개 식당/요리법 상세 파일은 만들지 않음.** 추후 실 데이터가 검증되면 페이지 생성 기능을 활성화할 기반만 준비.
- 기존 쿼리 상세 버튼은 그대로 남기고, 승인된 정적 경로가 있을 때만 '고정 주소로 보기' 링크 표시. route map 미로드 시 기존 UI 유지.
- 생성 페이지는 현재 Public 허용 필드만 표시하고 JS/CSS/공식 링크 소스 내부 매핑을 전달하지 않는다.

## SEO와 배포
- `SITE_ORIGIN` 환경변수를 실제 검증된 사이트 루트로 제공하면 절대 canonical/sitemap.xml 생성. 설정 전에는 둘 다 만들지 않고 GitHub Pages 프리뷰에서 상대 경로로 동작.
- 배포 URL의 경로 prefix (`/restaurant-site-public/` vs custom domain root `/`)는 `SITE_ORIGIN`에 포함되어야 한다.
- 페이지 탐색·새로고침/브라우저 직접 GET 200 테스트는 실제 승인 데이터가 들어온 단계에서 반드시 실시. 현재는 template + route 계약 테스트만 수행 가능.
- 외부 검색용 본문이 없는 식당은 색인용 정적 페이지를 생성하지 않는다. 장소/방송/주차·카드 연동은 승인된 데이터가 있어야 표시한다.
- 별도 embed URL/파라미터와 Tistory/Blogger 링크는 삭제하지 않음. `?embed=1` 기존 화면 우선 보존.
- 내부 예약·승인·검증 지표 없이 SEO용 수천 개 페이지 임의 발행 금지.

## 실행
```sh
python scripts/validate_public.py
python scripts/validate_recipes.py
python scripts/build_public_routes.py
python -m unittest discover -s tests -v
node --check app.js && node --check recipes.js
```
현재 예상 출력: `PASS: 0 approved deep-link routes`.

## 추후 작업
1. 실제 승인된 맛집/레시피 입력 시 공개 slug 정리, 이력/동명이점포 충돌 검사.
2. 브랜드/지역/개별점포 구조 및 이벤트 연결 정책과 ID 계약 통합 (카페 PR과 충돌 피함).
3. slug 유지 정책/리디렉션 alias 맵 마련, 실제 URL HTTP 검증, canonical/sitemap 최종 운영 설정 후 Search Console/Naver 등록.
4. Pages Actions 자동 생성/배포 설계, 필요 시 Cloudflare Pages 전환 검토. 현재 실제 서비스 배포 성공이라고 단정하지 않는다.
5. 실제 root domain 선택과 DNS 연결은 별도 승인 후에만 실행.
