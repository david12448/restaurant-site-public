"use strict";
// Approved recipe feed only. Public IDs and approved YouTube IDs are not private collector keys.
const $ = (id)=>document.getElementById(id);
const catalog={recipes:[],selected:null};
const regions={
  east_asia:"동아시아 · 한/중/일",southeast_asia:"동남아시아",
  south_asia:"남아시아 · 인도 등",west_asia_mena:"서아시아·아랍권·중동",
  europe:"유럽",africa:"아프리카",americas:"미주",oceania:"오세아니아",
  other:"그 밖의 음식권역"
};
const kinds={
  official_source:"공식 공개 레시피",adaptation:"편집 응용 레시피",
  broadcast_inspired:"방송 영감 레시피",editorial_original:"자체 작성 레시피"
};
const difficulty={easy:"쉬움",medium:"보통",advanced:"숙련"};
const params=new URLSearchParams(location.search);
if(params.get("embed")==="1")document.body.classList.add("embed");
function node(tag,text,cls){
  const e=document.createElement(tag);
  if(text!==undefined && text!==null)e.textContent=String(text);
  if(cls)e.className=cls;
  return e;
}
function append(parent,...children){children.forEach(c=>parent.appendChild(c));return parent}
function unique(items){return [...new Set(items)].sort((a,b)=>a.localeCompare(b,"ko"))}
function fill(selectId,options,defaultLabel){
  const select=$(selectId);select.replaceChildren();
  let base=node("option",defaultLabel);base.value="";select.appendChild(base);
  options.forEach(([value,label])=>{const e=node("option",label);e.value=value;select.appendChild(e)});
}
function setupFilters(){
  const regionCodes=unique(catalog.recipes.flatMap(r=>r.cuisine_regions||[]));
  const cats=unique(catalog.recipes.map(r=>r.category).filter(Boolean));
  fill("recipe-region",regionCodes.map(code=>[code,regions[code]||code]),"전 세계");
  fill("recipe-category",cats.map(v=>[v,v]),"모든 종류");
}
function matches(r){
  const q=$("recipe-keyword").value.trim().toLocaleLowerCase("ko");
  const phrase=[r.title,r.original_name,r.description,...(r.ingredients||[]).map(i=>i.name)].filter(Boolean).join(" ").toLocaleLowerCase("ko");
  if(q&&!phrase.includes(q))return false;
  if($("recipe-region").value&&!(r.cuisine_regions||[]).includes($("recipe-region").value))return false;
  if($("recipe-category").value&&r.category!==$("recipe-category").value)return false;
  const max=Number($("recipe-minutes").value);
  if(max&&r.prep_minutes+r.cook_minutes>max)return false;
  const media=$("recipe-media").value;
  if(media==="broadcast"&&!(r.broadcast_mentions||[]).length)return false;
  if(media==="youtube"&&!(r.youtube_videos||[]).length)return false;
  return true;
}
function recipeCard(r){
  const article=node("article",null,"card");
  append(article,node("h3",r.title),
      node("p",[...r.cuisine_regions.map(code=>regions[code]||code),r.category].join(" · "),"meta"));
  const tags=node("div",null,"pills");
  [difficulty[r.difficulty],(r.prep_minutes+r.cook_minutes)+"분",kinds[r.publication_kind]].forEach(s=>{
    tags.appendChild(node("span",s,"pill"));
  });
  article.appendChild(tags);
  article.appendChild(node("p","기본 "+r.servings+"인분 · 출처 검수 "+r.last_verified_at,"recipe-note"));
  const b=node("button","재료와 만드는 방법 보기","button");b.type="button";b.addEventListener("click",()=>openRecipe(r.recipe_id));
  article.appendChild(b);return article;
}
function render(){
  const selected=catalog.recipes.filter(matches);
  $("recipe-count").textContent=selected.length+"개";
  $("recipe-list").replaceChildren(...selected.map(recipeCard));
  const empty=$("recipe-empty");empty.hidden=selected.length>0;
  empty.textContent=!catalog.recipes.length?
    "아직 공개 승인된 레시피가 없습니다. 공식 레시피의 재료·조리 단계·사용권을 검토한 후 등록합니다.":
    "이 조건과 일치하는 승인된 레시피가 없습니다. 검색어와 필터를 변경해 보세요.";
  if(catalog.selected&&!selected.some(r=>r.recipe_id===catalog.selected))closeRecipe();
}
function section(view,label){const s=node("section",null,"section");s.appendChild(node("h3",label));view.appendChild(s);return s;}
function formatAmount(ingredient,servings,originalServings){
  if(typeof ingredient.amount!=="number")return ingredient.note||"적당량(원본 계량 미제공)";
  const v=ingredient.amount*servings/originalServings;
  const rounded=Math.round((v+Number.EPSILON)*100)/100;
  return String(rounded)+(ingredient.unit?" "+ingredient.unit:"")+
    (ingredient.note?" · "+ingredient.note:"");
}
function populateRecipe(r,servings){
  const view=$("recipe-detail");view.replaceChildren();view.hidden=false;view.classList.add("recipe-detail");
  const close=node("button","상세 닫기","back");close.type="button";close.addEventListener("click",closeRecipe);
  append(view,close,node("h2",r.title));
  if(r.original_name)view.appendChild(node("p","원어 표기: "+r.original_name,"recipe-dish"));
  if(r.description)view.appendChild(node("p",r.description));
  const meta=node("div",null,"meta-grid");
  [regions[r.cuisine_regions[0]]||r.cuisine_regions[0],
   (r.prep_minutes+r.cook_minutes)+"분(준비 "+r.prep_minutes+"분 / 조리 "+r.cook_minutes+"분)",
   "난이도 "+difficulty[r.difficulty],kinds[r.publication_kind]].forEach(t=>meta.appendChild(node("span",t,"recipe-chip")));
  view.appendChild(meta);
  const prov=node("div",null,"recipe-provenance");
  append(prov,node("strong","레시피 유형: "+kinds[r.publication_kind]),
    node("p","자료: "+r.source_credit.provider+" · 출처 검증일 "+r.source_credit.verified_at,"muted"));
  view.appendChild(prov);
  const ingredients=section(view,"재료");
  const control=node("div",null,"serve-control");
  control.appendChild(node("label","인분 조절"));
  const choice=node("select");choice.setAttribute("aria-label","인분 선택");
  const portions=unique([1,2,3,4,6,r.servings]);
  portions.forEach(x=>{const option=node("option",x+"인분");option.value=String(x);if(x===servings)option.selected=true;choice.appendChild(option)});
  choice.addEventListener("change",()=>populateRecipe(r,Number(choice.value)));
  control.appendChild(choice);ingredients.appendChild(control);
  const ul=node("ul",null,"ingredient-list");
  r.ingredients.forEach(i=>ul.appendChild(node("li",i.name+" — "+formatAmount(i,servings,r.servings))));
  ingredients.appendChild(ul);
  ingredients.appendChild(node("p","계량 가능한 재료만 비례 조정됩니다. 열처리 시간이나 '약간'의 양은 자동 변경하지 않습니다.","recipe-note"));
  const steps=section(view,"만드는 순서");
  const ol=node("ol",null,"step-list");
  r.steps.forEach(step=>ol.appendChild(node("li",step.instruction)));
  steps.appendChild(ol);
  if(r.broadcast_mentions?.length){
    const b=section(view,"방송에서 소개된 음식·조리법");
    const list=node("ul");
    r.broadcast_mentions.forEach(m=>{
      const relation={featured_recipe:"공개된 공식 조리법",inspired_by:"방송에서 영감",dish_appeared:"음식 등장"}[m.relation];
      list.appendChild(node("li",m.program+" · "+relation+(m.episode?" · "+m.episode:"")+" · "+m.verified_at));
    });b.appendChild(list);
  }
  if(r.youtube_videos?.length){
    const vids=section(view,"관련 요리 영상 · YouTube");
    r.youtube_videos.forEach(v=>{
      const a=node("a",v.title+" · "+v.channel+" (YouTube)","media-link");
      a.href="https://www.youtube.com/watch?v="+encodeURIComponent(v.video_id);
      a.target="_blank";a.rel="noopener noreferrer";
      vids.appendChild(a);
    });
  }
  if(r.associated_restaurant_ids?.length){
    const places=section(view,"이 음식과 연관된 맛집");
    places.appendChild(node("p","같은 음식의 판매 식당을 연결하며, 해당 음식점의 실제 조리법이라는 뜻은 아닙니다.","recipe-note"));
    r.associated_restaurant_ids.forEach(id=>{
      const a=node("a","연관 음식점 확인","media-link");
      a.href="./index.html?restaurant="+encodeURIComponent(id);
      places.appendChild(a);
    });
  }
  const foot=section(view,"검증 및 이용 안내");
  append(foot,node("p","레시피 확인일: "+r.last_verified_at,"muted"),
    node("p","알레르기와 재료 상태, 조리 환경에 따라 주의사항이 달라질 수 있습니다.","muted"));
  view.scrollIntoView({behavior:"smooth",block:"start"});
}
function openRecipe(id){
  const r=catalog.recipes.find(item=>item.recipe_id===id);
  if(!r)return;
  catalog.selected=id;populateRecipe(r,r.servings);
}
function closeRecipe(){catalog.selected=null;$("recipe-detail").hidden=true;$("recipe-detail").replaceChildren();}
["recipe-keyword","recipe-region","recipe-category","recipe-minutes","recipe-media"].forEach(id=>{
  $(id).addEventListener(id==="recipe-keyword"?"input":"change",render);
});
(async()=>{
  try{
    const response=await fetch("./data/recipes.json",{cache:"no-store"});
    if(!response.ok)throw Error("HTTP "+response.status);
    const feed=await response.json();
    if(feed.schema_version!=="1.0"||!Array.isArray(feed.recipes))throw Error("Invalid public feed");
    catalog.recipes=feed.recipes;
    setupFilters();render();
    const target=params.get("recipe");
    if(target&&catalog.recipes.some(r=>r.recipe_id===target))openRecipe(target);
  }catch(error){
    $("recipe-count").textContent="불러오기 실패";
    const box=$("recipe-empty");box.hidden=false;
    box.textContent="레시피 정보를 불러오지 못했습니다. 다시 접속해 주세요.";
    console.error("Public recipe feed unavailable:",error.message);
  }
})();
