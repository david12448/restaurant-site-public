import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT / "data" / "recipe-taxonomy.json"
SCHEMA=ROOT / "schema" / "recipe-feed.v1.schema.json"

class RecipeTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy=json.loads(DATA.read_text(encoding="utf-8"))
        cls.schema=json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_six_groups_include_requested_categories(self):
        groups={g["id"] for g in self.taxonomy["groups"]}
        self.assertEqual(groups,{"meal","bread_baking","dessert",
                                 "frozen_dessert","beverage","convenience_combo"})

    def test_subgroup_labels_are_unique_and_present(self):
        for group in self.taxonomy["groups"]:
            subs=group["subgroups"]
            self.assertGreaterEqual(len(subs),3)
            self.assertEqual(len({v["id"] for v in subs}),len(subs))
            self.assertTrue(all(x["label"] for x in subs))

    def test_style_tags_include_fusion_and_remix(self):
        tags={t["id"] for t in self.taxonomy["style_tags"]}
        self.assertTrue({"fusion","remix","convenience"} <= tags)

    def test_schema_food_groups_match_taxonomy(self):
        options=set(self.schema["$defs"]["recipe"]["properties"]["food_group"]["enum"])
        self.assertEqual(options,{g["id"] for g in self.taxonomy["groups"]})

    def test_legacy_feed_remains_empty_until_approved(self):
        current=json.loads((ROOT / "data" / "recipes.json").read_text(encoding="utf-8"))
        self.assertEqual(current["schema_version"],"1.0")
        self.assertEqual(current["recipes"],[])

    def test_page_has_all_filters(self):
        html=(ROOT / "recipes.html").read_text(encoding="utf-8")
        js=(ROOT / "recipes.js").read_text(encoding="utf-8")
        for select_id in ("recipe-group","recipe-category","recipe-region",
                          "recipe-style","recipe-source","recipe-minutes"):
            self.assertIn('id="'+select_id+'"',html)
            self.assertIn(select_id,js)

if __name__=="__main__":
    unittest.main()
