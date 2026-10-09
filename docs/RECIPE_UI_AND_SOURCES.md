# 레시피 UI v1 결정 — 2026-10-09

## 별도 주소, 동일 사이트
- 맛집: index.html
- 레시피: recipes.html
- 둘 다 독립 검색, 상단 링크, ?embed=1 대응
- 향후 음식 개념 `dish_id`를 가게 메뉴, 레시피, 방송 프로그램, 여행지 음식과 연결.
- 기존 식당 v1 schema를 파괴하지 않는다. 독립 버전 `recipe-feed.v1.schema.json`.

## 공개 데이터 경계
- 초기 approved recipes = 0. 샘플 가짜 요리·제작하지 않은 수치·방송에서 확인되지 않은 레시피는 공개하지 않음.
- 한식/중식/일식뿐 아니라 동남아·남아시아·서아시아/중동·아프리카·유럽·미주와 국가명을 **별도 다대다 필드**에 보관.
- 요리명 자체 `dish_id`, 다양한 조리법 각각 `recipe_id`, 세부 재료와 순서, 인분/시간/난이도, 매체·방송 연관 근거.
- 공식 동일 조리법 `official_source`; 공식 정보를 바탕으로 편집한 것은 `adaptation`; 프로그램에서 영감 받은 것은 `broadcast_inspired`; 사이트 자체 레시피는 `editorial_original`. 명칭/연관 자료는 엄격히 구분.
- 음식 하나 ↔ 여러 레시피, 레시피 ↔ 방송/인물/영상, 음식 ↔ 음식점 메뉴 연결.
- 유튜브/블로그 영상의 퍼가기·썸네일·검색·메타데이터 수집은 각 플랫폼 약관과 저작자 권리를 따름. 공개 영상 ID로만 유튜브 링크 연결 가능(선별 승인 후). 원본·전체 자막 무단 복제 불가.

## 영양 수치 및 주의
자료에 제공되더라도 중량 기준과 계산 근거가 확인되지 않았으면 별도 검토 전 공개하지 않음. 건강 효과, 다이어트 압박 등 강조 금지.
계량 미확인 '약간' 등을 수치로 억지 변환 금지. 초보자 안전을 고려해 조리 도구·알레르기 관련 정보의 확인 필요성 표시.

## 공식 출처
- 식약처 COOKRCP01 https://www.foodsafetykorea.go.kr/api/openApiInfo.do?menu_grp=MENU_GRP31&menu_no=661&svc_no=COOKRCP01
- YouTube 검색/영상 API https://developers.google.com/youtube/v3/docs/search/list
- 유튜브 개발자 정책 https://developers.google.com/youtube/terms/developer-policies
- 넷플릭스 흑백요리사 프로그램 https://www.netflix.com/kr/title/81728365

## 현 단계
완성된 공개 페이지 코드는 도입하지만 공식 레시피 실데이터 수집과 원문/사진 게시 허가 검증은 아직 진행되지 않았다. 출처 리뷰 후 승인된 레시피가 들어오면 단계별 UI가 작동한다.

## 레시피 범위 2차 확장 — 2026-10-09
- `food_group` : meal, bread_baking, dessert, frozen_dessert, beverage, convenience_combo. taxonomy(JSON)의 한국어 탭 레이블과 food_subgroup 분류를 사용.
- `style_tags`: traditional, fusion, remix, home_style, quick_easy, convenience. 큰 분류와 별도 필터.
- 출처국 `source_credit.source_country` / `cross_references`는 음식의 원산지를 뜻하지 않는다. KR과 외국이 함께 있으면 국내·해외 비교 필터에 나타낸다.
- 편의점 조합은 `combo_products`가 2개 이상 확인되어야 함. 각각 브랜드(있을 때)·상품명·포장/검증일 표시, 현재 재고가 있음을 암시하지 않는다.
- `serving_unit`/냉각·발효 `time_notes`는 케이크·아이스크림·음료의 단위/시간 혼동을 줄임.
- 신규 필드는 v1에서 선택적이므로 기존 승인 레시피를 파괴하지 않는다. 새 레시피는 반드시 food_group을 지정하는 편집 정책 유지.
- 레시피 출처 원문 무단 복사 금지, 해외 출처/원문/사진은 권리 검토 후. 공개용 카테고리/가이드만 승인, 실제 레시피는 0건 유지.
