"""Build physical, SEO-ready public pages only from approved restaurant/recipe feeds.

The current approved feeds are empty, so this publishes NO invented detail pages.
An explicit verified SITE_ORIGIN is required for canonical and sitemap.
"""
import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape as xml_escape

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.validate_public import validate as validate_restaurants
from scripts.validate_recipes import validate as validate_recipes

PATTERN=re.compile(r"^(restaurants|recipes)/[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*/$")
CATEGORIES={"restaurants":"restaurants","recipes":"recipes"}


def text(value):
    return html.escape(str(value if value is not None else ""),quote=True)


def site_origin():
    raw=os.environ.get("SITE_ORIGIN","").strip()
    if not raw:
        return None
    parsed=urlsplit(raw)
    if (parsed.scheme!="https" or not parsed.hostname or parsed.username or
        parsed.password or parsed.query or parsed.fragment or
        (parsed.path and not parsed.path.endswith("/"))):
        raise ValueError("SITE_ORIGIN must be verified HTTPS deployment root ending with /")
    return raw.rstrip("/")+"/"


def load():
    a=json.loads((ROOT/"data/restaurants.json").read_text(encoding="utf-8"))
    b=json.loads((ROOT/"data/recipes.json").read_text(encoding="utf-8"))
    validate_restaurants(a)
    validate_recipes(b)
    mapping=json.loads((ROOT/"data/url-routes.json").read_text(encoding="utf-8"))
    if not isinstance(mapping,dict) or set(mapping)!={"schema_version","restaurants","recipes"} or mapping["schema_version"]!="1.0":
        raise ValueError("Unsupported route manifest version")
    sources={"restaurants":a["restaurants"],"recipes":b["recipes"]}
    seen=set()
    for k,rows in sources.items():
        mp=mapping[k]
        if not isinstance(mp,dict) or set(mp)!={r["restaurant_id" if k=="restaurants" else "recipe_id"] for r in rows}:
            raise ValueError("Every approved detail needs exactly one reviewed pretty URL")
        for route in mp.values():
            if not isinstance(route,str) or not PATTERN.fullmatch(route) or not route.startswith(k+"/"):
                raise ValueError("Invalid or unsafe friendly route")
            if route in seen:
                raise ValueError("Duplicate friendly URL")
            seen.add(route)
    return sources,mapping


def render_restaurant(row):
    address=row.get("address_summary","").strip()
    if not address or not row.get("attribution") or not row.get("cuisine_tags"):
        raise ValueError("Restaurant detail has insufficient unique public information")
    status={"registered_active":"인허가 운영 상태 참고","registered_closed":"인허가 폐업 기록 참고","unknown":"현재 운영 상태 미확인"}.get(row["business_status"],"미확인")
    region=row["area"]
    return (row["name"],
        f'<p>지역: {text(region["sido"])} {text(region["sigungu"])}</p>'
        f'<p>주소 안내: {text(address)}</p>'
        f'<p>음식 종류: {text(", ".join(row["cuisine_tags"]))}</p>'
        f'<p>운영 정보: {text(status)} · 자료 확인일 {text(row["last_verified_at"])}</p>'
        f'<p>확인 근거 유형: {text(", ".join(row["attribution"]))}</p>'
        '<p>영업시간·주차·할인 등은 방문 전 해당 업체의 최신 안내로 다시 확인하세요.</p>'
    )


def render_recipe(row):
    ingredients="".join(
        "<li>"+text(i["name"])+
        (" · "+text(i["amount"])+(" "+text(i.get("unit","")) if i.get("unit") else "") if "amount" in i else "")+
        (" · "+text(i.get("note","")) if i.get("note") else "")+"</li>" for i in row["ingredients"])
    steps="".join("<li>"+text(s["instruction"])+"</li>" for s in row["steps"])
    return (row["title"],
        "<p>"+text(row.get("description","공개 검증된 요리법입니다."))+"</p>"
        "<p>기준 인분: "+text(row["servings"])+" · 준비 "+text(row["prep_minutes"])+"분 · 조리 "+text(row["cook_minutes"])+"분</p>"
        "<h2>재료</h2><ul>"+ingredients+"</ul><h2>조리 순서</h2><ol>"+steps+"</ol>"
        "<p>제공기관: "+text(row["source_credit"]["provider"])+" · 검증일 "+text(row["last_verified_at"])+"</p>"
        "<p>알레르기·재료 상태 및 도구 안전 안내는 원래 제품과 공식 제공 자료를 확인하세요.</p>"
    )


def build_page(title,body,route,origin):
    depth=len(route.rstrip("/").split("/"))
    prefix="../"*depth
    canonical=f'<link rel="canonical" href="{text(origin+route)}">' if origin else ""
    return f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{text(title)} | 맛집·레시피 안내</title>
<meta name="description" content="{text(title)} — 검증된 상세정보와 업데이트 날짜를 확인하세요.">
{canonical}
<link rel="stylesheet" href="{prefix}styles.css">
<style>.static-detail{{max-width:920px;margin:22px auto;padding:0 18px}}.static-detail article{{background:#fff;border:1px solid #dee4ed;border-radius:14px;padding:24px;line-height:1.7}}
.static-detail a{{color:#215783}}@media(max-width:570px){{.static-detail article{{padding:16px}}}}</style>
</head><body>
<header class="site-head"><div class="wrap"><h1>{text(title)}</h1>
<nav class="food-nav"><a href="{prefix}">맛집 찾기</a><a href="{prefix}recipes.html">레시피</a></nav></div></header>
<main class="static-detail"><nav><a href="{prefix}">← 전체 목록으로</a></nav>
<article><h2>확인된 내용</h2>{body}</article></main>
</body></html>
"""


def build():
    sources,mapping=load()
    origin=site_origin()
    routes=[]
    for category,rows in sources.items():
        key="restaurant_id" if category=="restaurants" else "recipe_id"
        for row in rows:
            path=mapping[category][row[key]]
            title,body=(render_restaurant(row) if category=="restaurants" else render_recipe(row))
            output=ROOT/path/"index.html"
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(build_page(title,body,path,origin),encoding="utf-8")
            routes.append(path)
    sitemap=ROOT/"sitemap.xml"
    if origin:
        urls=[origin]+[origin+r for r in sorted(routes)]
        xml='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        xml+="".join("  <url><loc>"+xml_escape(u)+"</loc></url>\n" for u in urls)+"</urlset>\n"
        sitemap.write_text(xml,encoding="utf-8")
    elif sitemap.exists():
        raise ValueError("Do not publish a sitemap for an unverified hostname")
    print("PASS:",len(routes),"approved deep-link routes; origin verified:",bool(origin))
    return len(routes)


if __name__=="__main__":
    build()
