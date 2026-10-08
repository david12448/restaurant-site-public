"use strict";
// Only approved feed reaches the browser. No collector, provider IDs or URLs.
const byId = (id) => document.getElementById(id);
const state = { restaurants: [], selected: null };
const isEmbed = new URLSearchParams(location.search).get("embed") === "1";
if (isEmbed) document.body.classList.add("embed");

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}
function add(parent, ...nodes) { nodes.forEach(node => parent.appendChild(node)); return parent; }
function verifiedStatus(item) {
  return item.status_alert && ["closed_confirmed", "relocated_confirmed"].includes(item.status_alert.kind);
}
function statusLabel(item) {
  if (!verifiedStatus(item)) return "";
  return item.status_alert.kind === "closed_confirmed" ? "폐업 확인" : "이전 확인";
}
function hasParking(item, type) {
  const p = item.parking || {};
  return type === "official" ? Boolean(p.official && p.official.availability !== "unknown") :
    Boolean(Array.isArray(p.visitor_reports) && p.visitor_reports.length);
}
function fillOptions() {
  const regions = [...new Set(state.restaurants.map(r => r.area && r.area.sido).filter(Boolean))].sort();
  const cuisines = [...new Set(state.restaurants.flatMap(r => r.cuisine_tags || []))].sort();
  for (const [id, options] of [["region",regions],["cuisine",cuisines]]) {
    const select = byId(id);
    select.replaceChildren(el("option", id === "region" ? "전국" : "전체 음식"));
    select.options[0].value = "";
    options.forEach(v => { const opt = el("option", v); opt.value = v; select.appendChild(opt); });
  }
}
function matches(r) {
  const term = byId("keyword").value.trim().toLocaleLowerCase("ko");
  const haystack = [r.name, r.address_summary, r.area?.sido, r.area?.sigungu, ...(r.cuisine_tags || [])].filter(Boolean).join(" ").toLocaleLowerCase("ko");
  if (term && !haystack.includes(term)) return false;
  if (byId("region").value && r.area?.sido !== byId("region").value) return false;
  if (byId("cuisine").value && !(r.cuisine_tags || []).includes(byId("cuisine").value)) return false;
  if (byId("parking").value && !hasParking(r, byId("parking").value)) return false;
  if (byId("media").value === "broadcast" && !(r.broadcasts || []).length) return false;
  if (byId("media").value === "celebrity" && !(r.celebrity_mentions || []).length) return false;
  return true;
}
function tags(parent, values) {
  const bar = el("div", null, "pills");
  values.filter(Boolean).forEach(v => bar.appendChild(el("span", v, "pill")));
  parent.appendChild(bar);
}
function card(item) {
  const box = el("article", null, "card");
  box.appendChild(el("h3", item.name));
  box.appendChild(el("p", [item.area?.sido,item.area?.sigungu,item.address_summary].filter(Boolean).join(" · "), "meta"));
  tags(box, [...(item.cuisine_tags || []).slice(0,3), (item.broadcasts || []).length ? "방송 소개" : "",
    (item.celebrity_mentions || []).length ? "연예인 언급" : "",
    hasParking(item,"official") ? "매장 주차 안내" : "",
    hasParking(item,"visitor") ? "방문자 주차 경험" : ""]);
  if (verifiedStatus(item)) box.appendChild(el("p", statusLabel(item) + " · 확인일 " + item.status_alert.verified_at, "notice"));
  else box.appendChild(el("p", "최근 정보 확인: " + (item.last_verified_at || "확인 필요"), "meta"));
  const btn = el("button","상세 정보 보기","button");
  btn.type="button"; btn.addEventListener("click",()=>showDetail(item.restaurant_id));
  box.appendChild(btn); return box;
}
function render() {
  const list=state.restaurants.filter(matches);
  byId("count").textContent=list.length+"곳";
  const cards=byId("cards"); cards.replaceChildren(...list.map(card));
  const empty=byId("empty"); empty.hidden=list.length!==0;
  empty.textContent=state.restaurants.length===0 ?
    "아직 검증을 마친 맛집이 없습니다. 방송·주차·주소·영업상태를 확인한 정보부터 순차적으로 등록합니다." :
    "해당 조건에 맞는 검증된 맛집이 없습니다. 다른 조건을 선택해 보세요.";
  if (state.selected && !list.some(r=>r.restaurant_id===state.selected)) hideDetail();
}
function line(parent,text,cls) {parent.appendChild(el("p",text,cls));}
function section(detail,title) { const div=el("section",null,"section");div.appendChild(el("h3",title));detail.appendChild(div);return div; }
function listOf(parent,entries,format,empty) {
  if(!entries.length) {line(parent,empty,"muted"); return;}
  const ul=el("ul"); entries.forEach(item=>ul.appendChild(el("li",format(item))));parent.appendChild(ul);
}
function showDetail(id) {
  const r=state.restaurants.find(v=>v.restaurant_id===id); if(!r)return;
  state.selected=id;
  const view=byId("detail"); view.replaceChildren(); view.hidden=false;
  const back=el("button","상세 닫기","back");back.type="button";back.addEventListener("click",hideDetail);
  add(view,back,el("h2",r.name));
  line(view,[r.area?.sido,r.area?.sigungu,r.address_summary].filter(Boolean).join(" · "),"meta");
  if (verifiedStatus(r)) {
    const alert=el("div",null,"alert");
    alert.setAttribute("role","alert");
    add(alert,el("strong",statusLabel(r)),el("p",r.status_alert.message || "매장 정보가 변경되었습니다."),
      el("p","확인일: "+r.status_alert.verified_at));
    view.appendChild(alert);
  } else line(view,"영업 정보 최종 확인: "+(r.last_verified_at||"미확인")+" · 현재 영업 중임을 보장하지 않습니다.","muted");

  const parking=section(view,"주차 안내");
  if (r.parking?.official) {
    const official=r.parking.official;
    line(parking,"매장 공식 안내 ("+(official.verified_at||"날짜 미확인")+"): "+(official.description || "세부 내용 없음"));
  } else line(parking,"매장 공식 주차 정보: 확인되지 않음","muted");
  const reports=r.parking?.visitor_reports||[];
  listOf(parking,reports,v=>"방문자 경험 ("+v.visited_at+"): "+v.location_label+
    (v.note ? " · "+v.note:"")+(v.walk_minutes!==undefined?" · 도보 약 "+v.walk_minutes+"분":""),
    "직접 제공받아 검증한 방문자 주차 경험이 없습니다.");
  line(parking,"주차 가능 여부·요금은 수시로 바뀝니다. 주차 규정을 지키고 방문 전에 확인하세요.","muted");

  const media=section(view,"방송·연예인 소개");
  listOf(media,r.broadcasts||[],v=>v.program+(v.episode?" · "+v.episode:"")+
    " · 방송일 "+(v.aired_on || "확인 필요")+
    (v.sponsored==="yes"?" · 협찬 표시":""),
    "확인된 방송 출연 자료가 없습니다.");
  listOf(media,r.celebrity_mentions||[],v=>v.person+" · "+
    ({visited:"방문 확인",recommended:"추천 확인",mentioned:"언급 확인"}[v.kind] || "언급")+
    " · 확인일 "+v.verified_at,
    "확인된 연예인 방문·추천 이력이 없습니다.");

  const reviews=section(view,"리뷰 지표 (제공처별)");
  listOf(reviews,r.review_metrics||[],v=>v.provider+" "+v.metric_label+" "+v.count.toLocaleString("ko-KR")+"건 · "+v.observed_at,
    "재이용 권한이 확인된 리뷰 수 데이터가 없습니다. 리뷰가 0건이라는 뜻은 아닙니다.");
  if(r.rating?.score!==undefined)line(reviews,r.rating.provider+" 평점 "+r.rating.score+" / "+r.rating.out_of+" · "+r.rating.observed_at);

  const history=section(view,"가게 이력");
  listOf(history,(r.history||[]).slice().sort((a,b)=>b.date.localeCompare(a.date)),
    v=>v.date+" · "+v.description,"확인된 이전·상호변경·폐업 이력이 없습니다.");
  const sources=section(view,"정보 확인");
  line(sources,"최종 검증일: "+(r.last_verified_at||"확인 필요"),"muted");
  line(sources,"출처 유형: "+((r.attribution||[]).join(", ")||"미확인"),"muted");
  line(sources,"공식 원본 링크는 검증된 서버 연결 기능이 준비된 이후 제공합니다.","muted");
  view.scrollIntoView({behavior:"smooth",block:"start"});
}
function hideDetail() {state.selected=null;byId("detail").hidden=true;byId("detail").replaceChildren();}
["keyword","region","cuisine","parking","media"].forEach(id=>{
  byId(id).addEventListener(id==="keyword"?"input":"change",render);
});
(async()=>{
  try {
    const response=await fetch("./data/restaurants.json",{cache:"no-store"});
    if(!response.ok)throw new Error("HTTP "+response.status);
    const payload=await response.json();
    if(payload.schema_version!=="1.0" || !Array.isArray(payload.restaurants))throw new Error("feed format");
    state.restaurants=payload.restaurants;
    fillOptions();
    render();
  }catch(error){
    byId("count").textContent="불러오기 실패";
    const empty=byId("empty");empty.hidden=false;
    empty.textContent="맛집 정보를 불러오지 못했습니다. 잠시 후 다시 확인해 주세요.";
    console.error("Public restaurant feed unavailable:",error.message);
  }
})();