"use strict";
const byId=id=>document.getElementById(id);
const names={discount:"직접 할인",coupon:"쿠폰",payment:"간편결제",subscription:"커피 구독",card:"제휴카드",loyalty:"멤버십·적립",merch:"굿즈·MD",menu_launch:"신메뉴 출시",telecom:"통신사 혜택"};
const data={brands:[],offers:[],selected:null};
const params=new URLSearchParams(location.search);
if(params.get("embed")==="1")document.body.classList.add("embed");
const create=(tag,text,cls)=>{const a=document.createElement(tag);if(text!=null)a.textContent=String(text);if(cls)a.className=cls;return a};
function kstToday(){return new Intl.DateTimeFormat("sv-SE",{timeZone:"Asia/Seoul",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date())}
function offerState(r){const t=kstToday();return t<r.starts_on?"upcoming":t>r.ends_on?"ended":"current"}
function brandName(id){return data.brands.find(x=>x.brand_id===id)?.name||"브랜드 확인 필요"}
function searchText(r){return [r.title,r.provider,...r.brand_ids.map(brandName),...r.terms].join(" ").toLocaleLowerCase("ko")}
function eligible(r){
  const q=byId("cafe-search").value.trim().toLocaleLowerCase("ko");
  if(q&&!searchText(r).includes(q))return false;
  if(byId("cafe-brand").value&&!r.brand_ids.includes(byId("cafe-brand").value))return false;
  if(byId("cafe-kind").value&&r.kind!==byId("cafe-kind").value)return false;
  if(byId("cafe-status").value!=="all"&&offerState(r)!==byId("cafe-status").value)return false;
  return true;
}
function fill(){
  const select=byId("cafe-brand");
  data.brands.forEach(b=>{const o=create("option",b.name);o.value=b.brand_id;select.appendChild(o)});
  const kinds=byId("cafe-kind");
  Object.entries(names).forEach(([k,v])=>{const o=create("option",v);o.value=k;kinds.appendChild(o)});
  const current=params.get("brand");if(data.brands.some(b=>b.brand_id===current))select.value=current;
}
function brandButtons(){
  const place=byId("brand-list");place.replaceChildren();
  data.brands.forEach(b=>{
    const btn=create("button",b.name,"brand-item");btn.type="button";
    btn.setAttribute("aria-pressed",String(byId("cafe-brand").value===b.brand_id));
    btn.addEventListener("click",()=>{
      byId("cafe-brand").value=byId("cafe-brand").value===b.brand_id?"":b.brand_id;
      render();
    });place.appendChild(btn);
  });
  byId("brand-count").textContent=data.brands.length+"개 브랜드";
}
function valueDescription(r){
  const v=r.value;if(!v||v.method==="none")return "금전 할인 정보 없음";
  if(v.method==="percent")return "확인된 기본 할인율 "+v.amount+"% (조건·한도 확인)";
  if(v.method==="fixed")return "확인된 기본 할인 "+v.amount.toLocaleString("ko-KR")+"원 (조건·한도 확인)";
  return "포인트·적립 혜택 (현금 할인과 합산하지 않음)";
}
function card(r){
  const p=create("article",null,"card");
  p.appendChild(create("h3",r.title));
  p.appendChild(create("p",r.brand_ids.map(brandName).join(" · ")+" · "+names[r.kind],"meta"));
  p.appendChild(create("p",r.starts_on+" ~ "+r.ends_on+" · "+({current:"기간 해당",ended:"종료",upcoming:"예정"}[offerState(r)]),"meta"));
  p.appendChild(create("p",valueDescription(r),"cafe-savings"));
  const btn=create("button","조건 자세히 보기","button");btn.type="button";
  btn.addEventListener("click",()=>showDetail(r.offer_id));p.appendChild(btn);
  return p;
}
function render(){
  brandButtons();
  const q=byId("cafe-search").value.trim().toLocaleLowerCase("ko");
  const filteredBrands=data.brands.filter(b=>[b.name,...b.aliases].join(" ").toLocaleLowerCase("ko").includes(q));
  if(q){
    const chosen=new Set(filteredBrands.map(b=>b.brand_id));
    const matched=data.offers.filter(r=>eligible(r)||r.brand_ids.some(x=>chosen.has(x))).filter(r=>
      (byId("cafe-kind").value===""||r.kind===byId("cafe-kind").value)&&
      (byId("cafe-status").value==="all"||offerState(r)===byId("cafe-status").value)&&
      (!byId("cafe-brand").value||r.brand_ids.includes(byId("cafe-brand").value)));
    renderOffers(matched);
  }else renderOffers(data.offers.filter(eligible));
  for(const b of byId("brand-list").children){
    const item=data.brands.find(x=>x.name===b.textContent);
    b.hidden=Boolean(q&&item&&!filteredBrands.includes(item));
  }
}
function renderOffers(items){
  byId("offer-list").replaceChildren(...items.map(card));
  byId("offer-count").textContent=items.length+"건";
  const empty=byId("offer-empty");
  empty.hidden=items.length>0;
  empty.textContent=data.offers.length===0?
    "아직 전체 조건을 확인해 게시 승인한 이벤트가 없습니다. 브랜드·결제사 원본을 검토해 업데이트할 예정입니다.":
    "해당 조건의 검증된 이벤트가 없습니다. 브랜드 또는 기간을 바꿔 보세요.";
  if(data.selected&&!items.some(o=>o.offer_id===data.selected))closeDetail();
}
function calculate(r,spend){
  const v=r.value||{};
  if(!Number.isFinite(spend)||spend<0)return null;
  if(v.method!=="percent"&&v.method!=="fixed")return null;
  if((v.min_payment_krw||0)>spend)return 0;
  const raw=v.method==="percent"?Math.floor(spend*v.amount/100):v.amount;
  return Math.min(spend,raw,v.max_discount_krw??Infinity);
}
function section(root,title){const s=create("section",null,"section");s.appendChild(create("h3",title));root.appendChild(s);return s}
function showDetail(id){
  const r=data.offers.find(x=>x.offer_id===id);if(!r)return;
  data.selected=id;
  const root=byId("cafe-detail");root.replaceChildren();root.hidden=false;
  const back=create("button","상세 닫기","back");back.type="button";back.addEventListener("click",closeDetail);
  root.appendChild(back);root.appendChild(create("h2",r.title));
  root.appendChild(create("p",r.brand_ids.map(brandName).join(", ")+" · "+r.provider+" · "+names[r.kind],"meta"));
  root.appendChild(create("p","혜택 기간 "+r.starts_on+" ~ "+r.ends_on+" / 최종 확인일 "+r.checked_on,"meta"));
  if(r.audience!=="general")root.appendChild(create("p","대상 고객 조건이 있습니다. 실제 계정 적용 여부를 확인하세요.","notice"));
  if(r.while_supplies_last)root.appendChild(create("p","수량 소진 가능: 기간 내라도 재고·쿠폰이 남아 있다는 뜻은 아닙니다.","notice"));
  const details=section(root,"조건·제한사항");
  const ul=create("ul",null,"offer-info-list");
  r.terms.forEach(v=>ul.appendChild(create("li",v)));
  details.appendChild(ul);
  if(r.availability_note)details.appendChild(create("p",r.availability_note));
  if(r.requires_app)details.appendChild(create("p","브랜드 또는 결제서비스 앱이 필요합니다.","cafe-fineprint"));
  if(r.requires_opt_in)details.appendChild(create("p","사전 응모 또는 쿠폰 신청이 필요합니다.","cafe-fineprint"));
  if(r.coupon_issue_from||r.coupon_issue_until)details.appendChild(create("p","쿠폰 발급 가능 기간: "+(r.coupon_issue_from||"미확인")+" ~ "+(r.coupon_issue_until||"미확인"),"meta"));
  details.appendChild(create("p",r.stacking==="unknown"?"중복 할인 여부 미확인: 다른 할인과 합산하지 않습니다.":r.stacking==="blocked"?"중복 할인 불가":"중복 적용 가능: 공식 조건별로 추가 확인 필요","cafe-fineprint"));
  const quote=section(root,"예상 할인액 참고");
  quote.appendChild(create("p",valueDescription(r)));
  if(r.kind==="subscription"){
    quote.appendChild(create("p","구독료와 쿠폰 사용 횟수를 따로 고려하세요. 구독 할인 전체를 1회 결제에 중복 적용하지 않습니다.","cafe-fineprint"));
  }else if(r.value&&["percent","fixed"].includes(r.value.method)){
    const wrap=create("div",null,"cafe-calc");
    const lab=create("label","결제 금액(원): ");
    const price=create("input");price.type="number";price.min="0";price.step="100";price.value="4500";price.setAttribute("aria-label","할인 계산용 결제 금액");
    const result=create("p",null,"cafe-savings");
    const change=()=>{
      const discount=calculate(r,Number(price.value));
      result.textContent=discount===null?"계산할 수 없습니다.":"조건 충족을 가정한 단일 혜택 예상 할인: "+discount.toLocaleString("ko-KR")+"원";
    };price.addEventListener("input",change);change();
    lab.appendChild(price);wrap.append(lab,result);quote.appendChild(wrap);
    quote.appendChild(create("p","실제 카드 실적·대상 매장·응모·적용 조건이 확인되지 않은 계산입니다. 타 이벤트 할인과 합산하지 않습니다.","cafe-fineprint"));
  }
  const proof=section(root,"출처·확인");
  proof.appendChild(create("p","검증 날짜: "+r.checked_on+" · 공식 원본 링크는 안전한 서버 연결이 준비된 경우에만 제공합니다.","meta"));
  root.scrollIntoView({behavior:"smooth",block:"start"});
}
function closeDetail(){data.selected=null;byId("cafe-detail").hidden=true;byId("cafe-detail").replaceChildren()}
for(const id of ["cafe-search","cafe-brand","cafe-kind","cafe-status"]){
  byId(id).addEventListener(id==="cafe-search"?"input":"change",render);
}
(async()=>{
  try{
    const [a,b]=await Promise.all([fetch("./data/cafe-brands.json"),fetch("./data/cafe-offers.json",{cache:"no-store"})]);
    if(!a.ok||!b.ok)throw Error("source not loaded");
    const [brandFeed,offerFeed]=await Promise.all([a.json(),b.json()]);
    if(brandFeed.schema_version!=="1.0"||offerFeed.schema_version!=="1.0")throw Error("wrong version");
    data.brands=brandFeed.brands;
    data.offers=offerFeed.offers;
    fill();render();
  }catch(e){
    byId("offer-count").textContent="불러오기 실패";
    const box=byId("offer-empty");box.hidden=false;
    box.textContent="카페 정보를 불러오지 못했습니다.";
    console.error("Cafe public feed error:",e.message);
  }
})();
