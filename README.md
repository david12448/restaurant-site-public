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
