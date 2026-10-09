"""Fail-closed public cafe data validation; retain private source map outside of public."""
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BRAND_ID=re.compile(r"^cafe_[a-z0-9]+$")
OFFER_ID=re.compile(r"^caf_[A-Za-z0-9_-]{8,80}$")
SOURCE_TOKEN=re.compile(r"^src_[A-Za-z0-9_-]{8,80}$")
RELATION=re.compile(r"^(card|payment|telecom):[a-zA-Z0-9:_-]+$")
LINK=re.compile(r"https?://|javascript:|data:|//",re.I)
BAD_KEYS={"source_url","official_url","provider_id","source_id","collector","parser",
          "original_html","raw_snapshot","api_key","redirect_map","card_number",
          "customer_id","customer_info","raw_text","review_text","image_url"}
FIELDS={"offer_id","brand_ids","title","kind","provider","starts_on","ends_on",
        "checked_on","terms","availability","audience","stacking","source_type",
        "verified","value","availability_note","coupon_issue_from","coupon_issue_until",
        "requires_opt_in","requires_app","while_supplies_last","financial_refs","source_token"}
MUST={"offer_id","brand_ids","title","kind","provider","starts_on","ends_on",
      "checked_on","terms","availability","audience","stacking","source_type","verified"}
KINDS={"discount","coupon","payment","subscription","card","loyalty","merch","menu_launch","telecom"}


def exact(obj,allowed,required=()):
    if not isinstance(obj,dict) or not set(required) <= set(obj) or not set(obj) <= set(allowed):
        raise ValueError("Unexpected or missing public fields")
    return obj


def date(s):
    if not isinstance(s,str):
        raise ValueError("Date must be ISO YYYY-MM-DD")
    try:
        if dt.date.fromisoformat(s).isoformat()!=s:
            raise ValueError("Invalid date")
    except ValueError as e:
        raise ValueError("Invalid calendar date") from e


def scrub(node):
    if isinstance(node,dict):
        for key,val in node.items():
            if key.lower() in BAD_KEYS:
                raise ValueError("Private internal field leaked into public: "+key)
            scrub(val)
    elif isinstance(node,list):
        for val in node: scrub(val)
    elif isinstance(node,str) and LINK.search(node):
        raise ValueError("Public data includes raw external URL")


def nonblank(x):
    if not isinstance(x,str) or not x.strip():
        raise ValueError("Missing text")


def check_brands(payload):
    exact(payload,{"schema_version","brands"},{"schema_version","brands"})
    if payload["schema_version"]!="1.0" or not isinstance(payload["brands"],list):
        raise ValueError("Invalid brand feed")
    scrub(payload)
    seen=set()
    for row in payload["brands"]:
        exact(row,{"brand_id","name","aliases"},{"brand_id","name","aliases"})
        if not isinstance(row["brand_id"],str) or not BRAND_ID.fullmatch(row["brand_id"]) or row["brand_id"] in seen:
            raise ValueError("Bad or duplicate cafe brand ID")
        seen.add(row["brand_id"])
        nonblank(row["name"])
        if not isinstance(row["aliases"],list) or any(not isinstance(a,str) or not a.strip() for a in row["aliases"]):
            raise ValueError("Bad brand aliases")
    return seen


def check_offers(payload,brands):
    exact(payload,{"schema_version","generated_at","offers"},{"schema_version","generated_at","offers"})
    if payload["schema_version"]!="1.0" or not isinstance(payload["offers"],list):
        raise ValueError("Invalid offer feed")
    if payload["generated_at"] is None:
        if payload["offers"]:
            raise ValueError("Approved offers require export timestamp")
    else:
        try:
            created=dt.datetime.fromisoformat(payload["generated_at"].replace("Z","+00:00"))
            if created.tzinfo is None:
                raise ValueError("Missing export timezone")
        except (TypeError,ValueError) as e:
            raise ValueError("Invalid generated_at") from e
    scrub(payload)
    seen=set()
    for row in payload["offers"]:
        exact(row,FIELDS,MUST)
        ident=row["offer_id"]
        if not isinstance(ident,str) or not OFFER_ID.fullmatch(ident) or ident in seen:
            raise ValueError("Bad or duplicate cafe offer")
        seen.add(ident)
        if (not isinstance(row["brand_ids"],list) or not row["brand_ids"] or
             len(set(row["brand_ids"]))!=len(row["brand_ids"]) or any(b not in brands for b in row["brand_ids"])):
            raise ValueError("Offer references unknown or duplicated cafe brand")
        for k in ("title","provider"):nonblank(row[k])
        if row["kind"] not in KINDS:
            raise ValueError("Unknown offer kind")
        for key in ("starts_on","ends_on","checked_on"):date(row[key])
        if row["starts_on"]>row["ends_on"]:
            raise ValueError("Offer has inverted dates")
        if not isinstance(row["terms"],list) or not row["terms"] or len(row["terms"])>20:
            raise ValueError("Approved offer needs its key conditions")
        for condition in row["terms"]:nonblank(condition)
        if row["availability"] not in ("nationwide","selected_stores","online_only","unknown"):
            raise ValueError("Unknown store scope")
        if row["audience"] not in ("general","new_user","members","targeted","unknown"):
            raise ValueError("Unknown audience")
        if row["stacking"] not in ("allowed","blocked","unknown"):
            raise ValueError("Unknown stacking relation")
        if row["source_type"] not in ("brand_official","card_official","payment_official","telecom_official"):
            raise ValueError("Unknown source type")
        if row["verified"] is not True:
            raise ValueError("Unreviewed offer cannot be published")
        for k in ("coupon_issue_from","coupon_issue_until"):
            if k in row: date(row[k])
        if (row.get("coupon_issue_from") and row.get("coupon_issue_until") and
                row["coupon_issue_from"]>row["coupon_issue_until"]):
            raise ValueError("Coupon issue window inverted")
        for k in ("requires_opt_in","requires_app","while_supplies_last"):
            if k in row and type(row[k]) is not bool:
                raise ValueError("Boolean field expected")
        if "availability_note" in row and (not isinstance(row["availability_note"],str) or len(row["availability_note"])>300):
            raise ValueError("Invalid availability note")
        if "source_token" in row and (not isinstance(row["source_token"],str) or not SOURCE_TOKEN.fullmatch(row["source_token"])):
            raise ValueError("Bad opaque source token")
        relations=row.get("financial_refs",[])
        if not isinstance(relations,list) or len(set(relations))!=len(relations):
            raise ValueError("Invalid financial refs")
        if any(not isinstance(rel,str) or not RELATION.fullmatch(rel) for rel in relations):
            raise ValueError("Invalid relation token")
        if "value" in row:
            val=exact(row["value"],{"method","amount","max_discount_krw","min_payment_krw",
                                     "subscription_fee_krw","per_use_limit"},{"method","amount"})
            if val["method"] not in ("percent","fixed","points","none"):
                raise ValueError("Invalid discount method")
            if type(val["amount"]) not in (int,float) or val["amount"]<0:
                raise ValueError("Invalid value amount")
            if val["method"]=="percent" and val["amount"]>100:
                raise ValueError("Discount exceeds 100 percent")
            if val["method"]=="none" and val["amount"]!=0:
                raise ValueError("No-value event cannot state a discount")
            for k in ("max_discount_krw","min_payment_krw","subscription_fee_krw","per_use_limit"):
                if k in val and (type(val[k]) is not int or val[k] < (1 if k=="per_use_limit" else 0)):
                    raise ValueError("Money/limit must be nonnegative integer")
        if row["kind"] in ("merch","menu_launch") and ("value" in row and row["value"]["method"] in ("percent","fixed")):
            raise ValueError("Merchandise/menu announcements are not assumed discounts")
        if row["kind"] in ("card","payment") and not row.get("financial_refs",[]):
            raise ValueError("Financial offer requires reviewed financial reference")
    return len(seen)


def main():
    try:
        brands=check_brands(json.loads((ROOT/"data/cafe-brands.json").read_text(encoding="utf-8")))
        offers=check_offers(json.loads((ROOT/"data/cafe-offers.json").read_text(encoding="utf-8")),brands)
        print("PASS: cafe public data",len(brands),"brands,",offers,"approved offers")
        return 0
    except (ValueError,OSError,TypeError,KeyError) as e:
        print("FAIL:",e,file=sys.stderr)
        return 1


if __name__=="__main__":
    sys.exit(main())
