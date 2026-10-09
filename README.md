# 전국 맛집 찾기 (Public)

방송 맛집, 연예인 공개 방문 기록, 공식·방문자 주차 정보, 주 2회 갱신 가능한 리뷰 관찰, 음식점 이전/폐업 사실 확인 이력을 분리해 보여주는 **공개 화면 기반 코드**입니다.

현재 approved 식당 데이터는 0건입니다. 실제 업체·가격·영업상태·방송 회차·평점은 미검증 값을 공개하지 않습니다.

## 보기
`python -m http.server 8000` 이후 브라우저에서 index.html.
여행/티스토리 임베드에는 `?embed=1` 사용.

## 검증
`python -m unittest discover -s tests -v`
`python scripts/validate_public.py` (실제 공개 JSON에 내부 원본 URL / provider ID / 개인 데이터 유출 차단)

## 분리
실제 인허가 상태/방송/리뷰/주차 데이터의 수집과 검증은 `restaurant-source-private`에만 존재. `restaurant_id` / `destination_ids` / `nearby_spot_ids`는 여행 서비스와 호환하도록 유지.

**상태:** 사이트 코드 개발 중; 라이브 맛집 수집 및 서비스 배포 확인 전.

## 레시피 영역 (신규)
- `recipes.html`: 세계 음식권역/재료/시간/방송 연관 필터 및 주문형 조리 단계 표시
- `data/recipes.json`: 공개 승인된 레시피만 (현재 0건)
- `schema/recipe-feed.v1.schema.json`: 음식 dish_id, 조리법 recipe_id, 구조화된 조리 단계, 편집 상태와 출처 검수.
- `scripts/validate_recipes.py`: 원본 URL·출처 키 등 공개 금지, 사용권 미승인·단계 오류의 발행 거부.
- 인분 조정은 계량치만; 실제 열처리 시간 등은 자동 보증하지 않음.
- `python scripts/validate_recipes.py` 후 `python -m unittest discover -s tests -v`로 점검.

## 세계 음식·디저트·편의점 레시피 확대
- 고정 탐색: 요리·식사 / 빵·베이킹 / 초콜릿·디저트 / 아이스크림·빙수 / 음료 / 편의점 꿀조합.
- 중복 검색 가능: 퓨전·변형 스타일, 국내/해외 출처·비교, 세계 음식권역, 세부 종류, 조리 시간, 방송/영상.
- `data/recipe-taxonomy.json`: 공통 세부분류. 신규 필드는 레시피 feed v1에 선택 필드로 추가해 기존 레시피에 대한 하위 호환 유지.
- 편의점 제품 구성/브랜드/확인일 및 국내·외국 교차근거는 이용권 승인과 실제 확인일 이후에만 공개.
- 실제 승인 레시피는 아직 0건. UI/수집 후보/테스트 완료와 실데이터 발행을 구별.
