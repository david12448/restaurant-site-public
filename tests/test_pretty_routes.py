import json
import unittest
from pathlib import Path
from scripts.build_public_routes import PATTERN, build, build_page, load

ROOT=Path(__file__).resolve().parents[1]

class FoodPrettyUrlTests(unittest.TestCase):
    def test_zero_approved_records_create_zero_detail_pages(self):
        sources, mapping=load()
        self.assertEqual(sum(map(len,sources.values())),0)
        self.assertEqual(mapping["restaurants"],{})
        self.assertEqual(mapping["recipes"],{})
        self.assertEqual(build(),0)

    def test_slugs_are_safe_and_hierarchical(self):
        self.assertIsNotNone(PATTERN.fullmatch("restaurants/seoul/garden-five/"))
        self.assertIsNotNone(PATTERN.fullmatch("recipes/bread-baking/baguette/"))
        self.assertIsNone(PATTERN.fullmatch("restaurants/seoul/../secret/"))
        self.assertIsNone(PATTERN.fullmatch("recipes/한식/비빔밥/"))
        self.assertIsNone(PATTERN.fullmatch("restaurants/seoul/some-id/?date=today"))

    def test_static_template_uses_portable_relative_links_and_escapes_user_data(self):
        html=build_page('<unsafe>',"<p>허가된 데이터</p>","restaurants/seoul/test-place/",None)
        self.assertIn("&lt;unsafe&gt;",html)
        self.assertNotIn("<unsafe>",html)
        self.assertIn('href="../../../styles.css"',html)
        self.assertNotIn('rel="canonical"',html)

    def test_domain_remains_undecided(self):
        config=json.loads((ROOT/"site.config.json").read_text(encoding="utf-8"))
        self.assertIsNone(config["public_origin"])
        self.assertFalse((ROOT/"CNAME").exists())
        self.assertFalse((ROOT/"sitemap.xml").exists())

if __name__=="__main__":
    unittest.main()
