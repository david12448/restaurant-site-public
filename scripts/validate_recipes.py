"""Fail-closed public recipe feed validation. Requires editorial + rights approval."""
import datetime as dt
import json
import re
import sys
from pathlib import Path

TOP={"schema_version","generated_at","recipes"}
RECIPE={"recipe_id","dish_id","title","original_name","description",
        "cuisine_regions","origin_countries","category","servings",
        "prep_minutes","cook_minutes","difficulty","ingredients","steps",
        "publication_kind","source_credit","last_verified_at",
        "associated_restaurant_ids","broadcast_mentions","youtube_videos",
        "food_group","food_subgroup","style_tags","preparation_methods",
        "serving_unit","time_notes","parent_recipe_id","combo_products","cross_references"}
REQUIRED={"recipe_id","dish_id","title","cuisine_regions","origin_countries",
          "category","servings","prep_minutes","cook_minutes","difficulty",
          "ingredients","steps","publication_kind","source_credit","last_verified_at"}
BAD={"url","source_url","raw_url","original_url","raw_snapshot","source_id",
     "provider_id","api_key","token","original_text","full_transcript",
     "article_html","parser","collector","license_plate","private_id"}
URL=re.compile(r"https?://|javascript:|data:",re.I)
ID=re.compile(r"^rcp_[A-Za-z0-9_-]{6,80}$")
DISH=re.compile(r"^dish_[A-Za-z0-9_-]{5,80}$")
RST=re.compile(r"^rst_[A-Za-z0-9_-]{6,80}$")
VID=re.compile(r"^[A-Za-z0-9_-]{11}$")


def fields(data, allowed, required):
    if not isinstance(data,dict) or not required <= set(data) or not set(data) <= allowed:
        raise ValueError("Unexpected or missing fields in public recipe object")
    return data


def date(value):
    if not isinstance(value,str) or dt.date.fromisoformat(value).isoformat()!=value:
        raise ValueError("Expected YYYY-MM-DD date")


def clean(data):
    if isinstance(data,dict):
        for k,v in data.items():
            if k.lower() in BAD:
                raise ValueError("Internal/sensitive key in public recipe data: "+k)
            clean(v)
    elif isinstance(data,list):
        for x in data: clean(x)
    elif isinstance(data,str) and URL.search(data):
        raise ValueError("Unexpected raw link in public recipe data")


def text(value):
    if not isinstance(value,str) or not value.strip():
        raise ValueError("Blank or invalid text")


def string_array(value, nonempty=False):
    if not isinstance(value,list) or (nonempty and not value):
        raise ValueError("Invalid label array")
    if any(not isinstance(x,str) or not x.strip() for x in value) or len(value)!=len(set(value)):
        raise ValueError("Invalid or repeated category label")


def validate(feed):
    fields(feed,TOP,TOP)
    if feed["schema_version"]!="1.0" or not isinstance(feed["recipes"],list):
        raise ValueError("Feed shape invalid")
    if feed["generated_at"] is None:
        if feed["recipes"]: raise ValueError("Populated feed needs an export timestamp")
    else:
        stamp=dt.datetime.fromisoformat(feed["generated_at"].replace("Z","+00:00"))
        if stamp.tzinfo is None: raise ValueError("Export timestamp requires timezone")
    clean(feed)
    taxonomy=json.loads((Path(__file__).resolve().parents[1]/"data/recipe-taxonomy.json").read_text(encoding="utf-8"))
    groups={g["id"]: {i["id"] for i in g["subgroups"]} for g in taxonomy["groups"]}
    styles={tag["id"] for tag in taxonomy["style_tags"]}
    methods={tag["id"] for tag in taxonomy["preparation_methods"]}
    seen=set()
    for item in feed["recipes"]:
        fields(item,RECIPE,REQUIRED)
        if not isinstance(item["recipe_id"],str) or not ID.fullmatch(item["recipe_id"]) or item["recipe_id"] in seen:
            raise ValueError("Invalid or duplicated recipe_id")
        seen.add(item["recipe_id"])
        if not isinstance(item["dish_id"],str) or not DISH.fullmatch(item["dish_id"]):
            raise ValueError("Invalid dish_id")
        for prop in ("title","category"): text(item[prop])
        for prop in ("cuisine_regions","origin_countries"):
            string_array(item[prop], prop=="cuisine_regions")
        if item["difficulty"] not in ("easy","medium","advanced"):
            raise ValueError("Unknown difficulty")
        for field in ("servings","prep_minutes","cook_minutes"):
            x=item[field]
            if type(x) is not int or x < (1 if field=="servings" else 0) or x>1440:
                raise ValueError("Invalid servings or minutes")
        if item["servings"] > 100:
            raise ValueError("Servings exceed approved limit")
        if item["publication_kind"] not in ("official_source","adaptation","broadcast_inspired","editorial_original"):
            raise ValueError("Publication kind unsupported")
        credit=fields(item["source_credit"],{"provider","license_verified","verified_at","source_country","language"},
                      {"provider","license_verified","verified_at"})
        text(credit["provider"])
        if credit["license_verified"] is not True:
            raise ValueError("Recipe reuse rights not approved")
        date(credit["verified_at"])
        date(item["last_verified_at"])
        group=item.get("food_group","meal")
        if group not in groups:
            raise ValueError("Unknown recipe food group")
        if "food_subgroup" in item and item["food_subgroup"] not in groups[group]:
            raise ValueError("Subgroup does not belong to food group")
        for field, allowed in (("style_tags",styles),("preparation_methods",methods)):
            string_array(item.get(field, []))
            if not set(item.get(field,[])) <= allowed:
                raise ValueError("Unknown recipe tag: "+field)
        if "serving_unit" in item and item["serving_unit"] not in ("serving","piece","cup","batch"):
            raise ValueError("Invalid portion unit")
        if "time_notes" in item and (not isinstance(item["time_notes"],str) or len(item["time_notes"])>300):
            raise ValueError("Invalid timing note")
        if "parent_recipe_id" in item and (not isinstance(item["parent_recipe_id"],str) or
            not ID.fullmatch(item["parent_recipe_id"]) or item["parent_recipe_id"]==item["recipe_id"]):
            raise ValueError("Invalid recipe derivation link")
        products=item.get("combo_products", [])
        if not isinstance(products,list):
            raise ValueError("Invalid convenience combo products")
        if group=="convenience_combo" and len(products)<2:
            raise ValueError("A convenience combo needs at least two documented products")
        if products and group!="convenience_combo":
            raise ValueError("Packaged convenience components require convenience_combo food_group")
        seen_products=set()
        for component in products:
            fields(component,{"product_name","brand","package","checked_at","substitution_note"},
                   {"product_name","checked_at"})
            text(component["product_name"])
            date(component["checked_at"])
            if any(not isinstance(component.get(k),str) for k in ("brand","package","substitution_note") if k in component):
                raise ValueError("Invalid brand or package notes")
            product_key=(component.get("brand","").casefold(),component["product_name"].casefold())
            if product_key in seen_products:
                raise ValueError("Duplicated packaged component")
            seen_products.add(product_key)
        for field in ("source_country", "language"):
            if field in credit:
                value=credit[field]
                rule=r"^[A-Z]{2}$" if field=="source_country" else r"^[a-z]{2,3}(?:-[A-Za-z0-9]+)*$"
                if not isinstance(value,str) or not re.fullmatch(rule,value):
                    raise ValueError("Invalid source locale")
        for other in item.get("cross_references", []):
            fields(other,{"provider","source_country","language","relation","verified_at"},
                   {"provider","source_country","language","relation","verified_at"})
            text(other["provider"])
            if not isinstance(other["source_country"],str) or not re.fullmatch(r"[A-Z]{2}",other["source_country"]):
                raise ValueError("Invalid foreign reference country")
            if not isinstance(other["language"],str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]+)*",other["language"]):
                raise ValueError("Invalid foreign reference language")
            if other["relation"] not in ("comparison","inspiration","supporting"):
                raise ValueError("Unknown cross-source relation")
            date(other["verified_at"])
        if not isinstance(item["ingredients"],list) or not item["ingredients"]:
            raise ValueError("Ingredients missing")
        for ing in item["ingredients"]:
            fields(ing,{"name","amount","unit","note"},{"name"})
            text(ing["name"])
            if "amount" in ing and (type(ing["amount"]) not in (float,int) or ing["amount"]<=0):
                raise ValueError("Invalid numeric ingredient amount")
            if "unit" in ing:
                text(ing["unit"])
                if "amount" not in ing:
                    raise ValueError("Unit without numeric amount")
            if "note" in ing and not isinstance(ing["note"],str):
                raise ValueError("Ingredient note must be text")
        if not isinstance(item["steps"],list) or not item["steps"]:
            raise ValueError("Ordered steps missing")
        for n,step in enumerate(item["steps"],1):
            fields(step,{"order","instruction"},{"order","instruction"})
            if type(step["order"]) is not int or step["order"]!=n:
                raise ValueError("Steps must be consecutive, ordered from 1")
            text(step["instruction"])
        string_array(item.get("associated_restaurant_ids",[]))
        if any(not RST.fullmatch(x) for x in item.get("associated_restaurant_ids",[])):
            raise ValueError("Unknown linked restaurant format")
        for b in item.get("broadcast_mentions",[]):
            fields(b,{"program","relation","verified_at","episode"},
                   {"program","relation","verified_at"})
            text(b["program"])
            if b["relation"] not in ("featured_recipe","inspired_by","dish_appeared"):
                raise ValueError("Broadcast relation unverified")
            date(b["verified_at"])
        for v in item.get("youtube_videos",[]):
            fields(v,{"video_id","title","channel","verified_at"},
                   {"video_id","title","channel","verified_at"})
            if not isinstance(v["video_id"],str) or not VID.fullmatch(v["video_id"]):
                raise ValueError("Invalid approved YouTube ID")
            text(v["title"]); text(v["channel"]); date(v["verified_at"])
    return len(seen)


if __name__=="__main__":
    try:
        fn=Path(sys.argv[1] if len(sys.argv)>1 else "data/recipes.json")
        count=validate(json.loads(fn.read_text(encoding="utf-8")))
        print("PASS: Approved recipe feed with",count,"recipes")
    except (ValueError,TypeError,OSError,json.JSONDecodeError) as err:
        print("FAIL:",err,file=sys.stderr)
        sys.exit(1)
