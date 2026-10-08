import copy
import unittest
from scripts.validate_public import validate


class PublicFeedTests(unittest.TestCase):
    def setUp(self):
        self.row={"restaurant_id":"rst_demo1234","name":"가상의 테스트 식당",
                  "area":{"sido":"서울특별시","sigungu":"종로구"},
                  "destination_ids":["dst_jongno_demo"],"cuisine_tags":["한식"],
                  "business_status":"unknown","last_verified_at":"2026-10-09",
                  "attribution":["테스트"]}
        self.feed={"schema_version":"1.0","generated_at":"2026-10-09T04:00:00+09:00",
                   "restaurants":[self.row]}

    def test_empty_feed(self):
        self.assertEqual(validate({"schema_version":"1.0","generated_at":None,"restaurants":[]}),0)

    def test_valid_test_fixture(self):
        self.assertEqual(validate(self.feed),1)

    def test_no_raw_url_or_source_id(self):
        for key in ("source_url","source_id","api_key"):
            p=copy.deepcopy(self.feed)
            p["restaurants"][0][key]="https://example.com"
            with self.assertRaises(ValueError):
                validate(p)

    def test_no_unverified_closure_warning(self):
        self.row["status_alert"]={"kind":"closed_confirmed","message":"폐업","verified_at":"2026-10-09"}
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_verified_warning_requires_history(self):
        self.row["status_alert"]={"kind":"closed_confirmed","message":"폐업","verified_at":"2026-10-09"}
        self.row["history"]=[{"date":"2026-10-09","kind":"closed_confirmed","description":"공식 확인"}]
        self.assertEqual(validate(self.feed),1)

    def test_parking_and_review(self):
        self.row["parking"]={"official":{"availability":"on_site","description":"매장 안내",
                                          "verified_at":"2026-10-09"},
                             "visitor_reports":[{"location_label":"공영주차장","visited_at":"2026-10-06",
                                                 "walk_minutes":5}]}
        self.row["review_metrics"]=[{"provider":"naver","metric_label":"방문자 리뷰",
                                     "count":312,"observed_at":"2026-10-09"}]
        self.assertEqual(validate(self.feed),1)

    def test_reject_unknown_nested_property(self):
        self.row["parking"]={"official":{"availability":"on_site","description":"안내",
                                          "verified_at":"2026-10-09",
                                          "original_url":"https://bad.example"}}
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_unknown_reviews_not_zero(self):
        self.assertNotIn("review_metrics",self.row)


if __name__=="__main__":
    unittest.main()
