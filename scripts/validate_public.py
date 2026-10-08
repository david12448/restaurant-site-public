"""Fail-closed validator for the approved public restaurant feed.

No source URLs, source/provider IDs, original reviews, private directory paths,
collector metadata or sensitive information are permitted in the public feed.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

TOP = {"schema_version", "generated_at", "restaurants"}
ITEM = {"restaurant_id", "name", "area", "destination_ids", "nearby_spot_ids",
        "address_summary", "cuisine_tags", "business_status", "last_verified_at",
        "attribution", "status_alert", "parking", "broadcasts",
        "celebrity_mentions", "review_metrics", "rating", "history"}
REQUIRED = {"restaurant_id", "name", "area", "destination_ids", "cuisine_tags",
            "business_status", "last_verified_at", "attribution"}
FORBIDDEN = {"url", "source_url", "original_url", "detail_url", "source_id", "provider_id",
             "raw_snapshot", "raw_data", "api_key", "redirect_map", "source_registry",
             "collector", "parser", "telephone", "phone", "visitor_name", "reporter_ip",
             "license_plate", "review_text", "raw_review"}
ID_PATTERN = re.compile(r"^rst_[A-Za-z0-9_-]{6,80}$")
URL_PATTERN = re.compile(r"https?://|javascript:|data:", re.IGNORECASE)


def ensure_private_fields_absent(item):
    if isinstance(item, dict):
        for key, value in item.items():
            if key.casefold() in FORBIDDEN:
                raise ValueError("internal field in public payload: " + key)
            ensure_private_fields_absent(value)
    elif isinstance(item, list):
        for value in item:
            ensure_private_fields_absent(value)
    elif isinstance(item, str) and URL_PATTERN.search(item):
        raise ValueError("URL or executable text in public payload")


def date_string(value):
    if not isinstance(value, str):
        raise ValueError("expected ISO date")
    try:
        if dt.date.fromisoformat(value).isoformat() != value:
            raise ValueError("invalid calendar date")
    except ValueError:
        raise ValueError("invalid YYYY-MM-DD date") from None


def obj(value, allowed, required=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or not set(value) <= set(allowed):
        raise ValueError("invalid or unexpected object fields")
    return value


def strings(value):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError("expected array of nonempty strings")
    if len(value) != len(set(value)):
        raise ValueError("duplicate tags")
    return value


def observations(item):
    if "parking" in item:
        parking = obj(item["parking"], ("official", "visitor_reports"))
        if "official" in parking:
            info = obj(parking["official"], ("availability","description","verified_at"),
                       ("availability","description","verified_at"))
            if info["availability"] not in {"on_site","partner","not_available","unknown"}:
                raise ValueError("invalid official parking availability")
            if not isinstance(info["description"], str):
                raise ValueError("invalid parking description")
            date_string(info["verified_at"])
        for p in parking.get("visitor_reports", []):
            p = obj(p, ("location_label","visited_at","note","walk_minutes"), ("location_label","visited_at"))
            if not isinstance(p["location_label"], str) or not p["location_label"].strip():
                raise ValueError("visitor parking location missing")
            date_string(p["visited_at"])
            if "note" in p and not isinstance(p["note"], str):
                raise ValueError("invalid parking note")
            if "walk_minutes" in p and (type(p["walk_minutes"]) is not int or p["walk_minutes"] < 0 or p["walk_minutes"] > 240):
                raise ValueError("invalid walking estimate")
    for b in item.get("broadcasts", []):
        b = obj(b, ("program","aired_on","sponsored","episode"),
                ("program","aired_on","sponsored"))
        if not isinstance(b["program"], str) or not b["program"].strip():
            raise ValueError("invalid program")
        date_string(b["aired_on"])
        if b["sponsored"] not in {"yes","no","unknown"}:
            raise ValueError("invalid sponsorship")
        if "episode" in b and not isinstance(b["episode"], str):
            raise ValueError("invalid episode")
    for mention in item.get("celebrity_mentions", []):
        mention = obj(mention, ("person","kind","verified_at"),
                      ("person","kind","verified_at"))
        if not isinstance(mention["person"], str) or not mention["person"].strip():
            raise ValueError("invalid person")
        if mention["kind"] not in {"visited","recommended","mentioned"}:
            raise ValueError("invalid mention")
        date_string(mention["verified_at"])
    for metric in item.get("review_metrics", []):
        metric = obj(metric, ("provider","metric_label","count","observed_at"),
                     ("provider","metric_label","count","observed_at"))
        if metric["provider"] not in {"naver","kakao","first_party"}:
            raise ValueError("unknown metric provider")
        if not isinstance(metric["metric_label"], str) or not metric["metric_label"].strip():
            raise ValueError("review metric name missing")
        if type(metric["count"]) is not int or metric["count"] < 0:
            raise ValueError("invalid review count")
        date_string(metric["observed_at"])
    if "rating" in item:
        r = obj(item["rating"], ("provider","score","out_of","observed_at"),
                ("provider","score","out_of","observed_at"))
        if r["provider"] not in {"naver","kakao","first_party"}:
            raise ValueError("unknown rating provider")
        if any(type(r[k]) not in (int, float) for k in ("score","out_of")) or r["out_of"] <= 0 or not 0 <= r["score"] <= r["out_of"]:
            raise ValueError("invalid rating")
        date_string(r["observed_at"])
    for h in item.get("history", []):
        h = obj(h, ("date","kind","description"), ("date","kind","description"))
        if h["kind"] not in {"opened","temporarily_closed","closed_confirmed","relocated_confirmed","renamed_confirmed","reopened"}:
            raise ValueError("unknown history event")
        if not isinstance(h["description"], str) or not h["description"].strip():
            raise ValueError("history event description required")
        date_string(h["date"])
    if "status_alert" in item:
        s = obj(item["status_alert"], ("kind","message","verified_at"),
                ("kind","message","verified_at"))
        if s["kind"] not in {"closed_confirmed","relocated_confirmed"}:
            raise ValueError("unconfirmed warning would mislead")
        if not isinstance(s["message"], str) or not s["message"].strip():
            raise ValueError("missing alert explanation")
        date_string(s["verified_at"])
        if not any(e["kind"] == s["kind"] for e in item.get("history", [])):
            raise ValueError("confirmed warning requires corroborated history entry")


def validate(feed):
    obj(feed, TOP, TOP)
    if feed["schema_version"] != "1.0" or not isinstance(feed["restaurants"], list):
        raise ValueError("invalid feed version or restaurant list")
    if feed["generated_at"] is None and feed["restaurants"]:
        raise ValueError("published restaurants require generated_at")
    elif feed["generated_at"] is not None:
        try:
            stamp = dt.datetime.fromisoformat(feed["generated_at"].replace("Z","+00:00"))
        except (AttributeError, ValueError):
            raise ValueError("invalid generation timestamp") from None
        if stamp.tzinfo is None:
            raise ValueError("timestamp timezone missing")
    ensure_private_fields_absent(feed)
    ids = set()
    for item in feed["restaurants"]:
        obj(item, ITEM, REQUIRED)
        ident = item["restaurant_id"]
        if not isinstance(ident, str) or not ID_PATTERN.fullmatch(ident) or ident in ids:
            raise ValueError("invalid or duplicate restaurant ID")
        ids.add(ident)
        if not isinstance(item["name"], str) or not item["name"].strip():
            raise ValueError("missing name")
        area = obj(item["area"], ("sido","sigungu","sido_code","sigungu_code"), ("sido","sigungu"))
        if any(not isinstance(area[k], str) or not area[k].strip() for k in ("sido","sigungu")):
            raise ValueError("invalid area")
        for key in ("destination_ids","cuisine_tags","attribution"):
            strings(item[key])
        for key in ("nearby_spot_ids",):
            if key in item:
                strings(item[key])
        if "address_summary" in item and not isinstance(item["address_summary"], str):
            raise ValueError("invalid address summary")
        if item["business_status"] not in {"registered_active","registered_closed","unknown"}:
            raise ValueError("invalid business_status")
        date_string(item["last_verified_at"])
        observations(item)
    return len(ids)


def main():
    path=Path(sys.argv[1] if len(sys.argv)>1 else "data/restaurants.json")
    try:
        count=validate(json.loads(path.read_text(encoding="utf-8")))
        print("PASS: approved public restaurant feed; records:",count)
        return 0
    except (ValueError, OSError, TypeError) as error:
        print("FAIL: "+str(error), file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
