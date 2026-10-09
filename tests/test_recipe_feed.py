import copy
import unittest
from scripts.validate_recipes import validate


class RecipeFeedTest(unittest.TestCase):
    def setUp(self):
        self.recipe={
            "recipe_id":"rcp_test0001","dish_id":"dish_test01",
            "title":"가상 조리법 테스트", "cuisine_regions":["east_asia"],
            "origin_countries":["KR"],"category":"밥",
            "servings":2,"prep_minutes":5,"cook_minutes":10,"difficulty":"easy",
            "ingredients":[{"name":"재료","amount":100,"unit":"g"},
                           {"name":"간","note":"기호에 맞게"}],
            "steps":[{"order":1,"instruction":"준비한다."},
                     {"order":2,"instruction":"완성한다."}],
            "publication_kind":"editorial_original",
            "source_credit":{"provider":"editorial_test_only","license_verified":True,
                             "verified_at":"2026-10-09"},
            "last_verified_at":"2026-10-09"
        }
        self.feed={"schema_version":"1.0","generated_at":"2026-10-09T00:00:00+09:00",
                   "recipes":[self.recipe]}

    def test_empty_is_valid(self):
        self.assertEqual(validate({"schema_version":"1.0","generated_at":None,"recipes":[]}),0)

    def test_mock_approved(self):
        self.assertEqual(validate(self.feed),1)

    def test_refuse_unapproved_licensed_record(self):
        self.recipe["source_credit"]["license_verified"]=False
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_refuse_private_url(self):
        self.recipe["source_url"]="https://private.example/secret"
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_step_order(self):
        self.recipe["steps"][1]["order"]=3
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_invalid_amount(self):
        self.recipe["ingredients"][0]["amount"]=-3
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_no_broadcast_without_evidence(self):
        self.recipe["broadcast_mentions"]=[{"program":"가상 방송","relation":"unverified",
                                             "verified_at":"2026-10-09"}]
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_recipe_identity_unique(self):
        self.feed["recipes"].append(copy.deepcopy(self.recipe))
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_safe_approved_youtube_reference(self):
        self.recipe["youtube_videos"]=[{"video_id":"AbCdEfGh123","title":"데모",
                                          "channel":"테스트","verified_at":"2026-10-09"}]
        self.assertEqual(validate(self.feed),1)



    def test_extended_global_food_group_and_cross_references(self):
        self.recipe["food_group"]="bread_baking"
        self.recipe["food_subgroup"]="bread"
        self.recipe["style_tags"]=["fusion"]
        self.recipe["preparation_methods"]=["oven"]
        self.recipe["source_credit"]["source_country"]="KR"
        self.recipe["source_credit"]["language"]="ko"
        self.recipe["cross_references"]=[
            {"provider":"Official International Recipe Reference",
             "source_country":"JP","language":"ja","relation":"comparison",
             "verified_at":"2026-10-09"}]
        self.assertEqual(validate(self.feed),1)

    def test_group_subgroup_mismatch_rejected(self):
        self.recipe["food_group"]="beverage"
        self.recipe["food_subgroup"]="bread"
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_unknown_remix_label_rejected(self):
        self.recipe["style_tags"]=["unverified_trend"]
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_combo_requires_two_real_product_descriptions(self):
        self.recipe["food_group"]="convenience_combo"
        self.recipe["food_subgroup"]="instant_noodles"
        self.recipe["style_tags"]=["remix","convenience"]
        self.recipe["combo_products"]=[
            {"product_name":"가상 라면 A","checked_at":"2026-10-09"}]
        with self.assertRaises(ValueError):
            validate(self.feed)
        self.recipe["combo_products"].append(
            {"product_name":"가상 소스 B","checked_at":"2026-10-09"})
        self.assertEqual(validate(self.feed),1)

    def test_duplicate_combo_products_rejected(self):
        self.recipe["food_group"]="convenience_combo"
        product={"product_name":"가상 치즈","brand":"가상 브랜드",
                 "checked_at":"2026-10-09"}
        self.recipe["combo_products"]=[product,dict(product)]
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_foreign_reference_invalid_country_rejected(self):
        self.recipe["cross_references"]=[
            {"provider":"Test Source","source_country":"한국",
             "language":"ko","relation":"comparison","verified_at":"2026-10-09"}]
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_self_parent_recipe_ref_rejected(self):
        self.recipe["parent_recipe_id"]=self.recipe["recipe_id"]
        with self.assertRaises(ValueError):
            validate(self.feed)

    def test_old_v1_recipe_has_backward_compatibility(self):
        self.assertNotIn("food_group",self.recipe)
        self.assertEqual(validate(self.feed),1)


if __name__=="__main__":
    unittest.main()
