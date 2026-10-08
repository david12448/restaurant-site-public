# Restaurant public site rules

- 먼저 docs/PRODUCT_DECISIONS.md와 GitHub 최신 상태/CI 확인.
- 공식/허가된 데이터만 공개. 수집기, 후보 검수, 원본 URL, 원본 provider ID, source_registry, parser, API 키, 원문 후기·영상·주차 제보 원문은 private만.
- 리뷰 수/평점은 허가된 수치만 출처별·종류별·측정일을 함께 표시. 없는 값은 0으로 표시하지 않음. 검색 API sort=comment로 리뷰 수 추정 금지.
- 방송 출연·연예인 방문은 실제 근거 검수된 식당만 노출. 협찬 및 게시일 표현을 왜곡하지 않음.
- 주차는 '매장 공식'과 '방문자 제보'를 분리하며 합법 주차 전제와 제보 날짜를 표시. 개인정보 노출 금지.
- 영업중(실시간)을 암시하지 않음. 폐점/이전 공식 확인된 경우 상단 경고+하단 가게 이력 병행; 검색 무응답만으로 폐점 경고 금지.
- UI는 지역/음식종류/주차/방송 필터, 상세 정보, 모바일과 iframe 임베드(?embed=1)를 지원.
- 공식 외부 링크는 실제 server redirect 준비 전에는 /go/id 가짜 링크를 만들지 않음. public 필드에는 token만, 매핑은 private.
- 여행 서비스는 v1 `restaurant_id` + `destination_ids` + `nearby_spot_ids` 계약으로 데이터만 연결.
- 편집글을 무단 복제하지 않음. 공개 정보를 완전히 F12에서 숨길 수는 없으며 내부 원본/수집자산을 애초에 전달하지 않는 게 핵심.
- 자동 머지/배포 성공이라고 말하기 전 Actions 결과 직접 확인.
