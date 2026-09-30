(()=>{
  const c=window.MONETIZE_CONFIG||{};
  const params=new URLSearchParams(location.search);
  const source=params.get("utm_source")||document.referrer||"direct";
  const log=(type,detail={})=>{
    const event={type,detail,source,path:location.pathname,ts:new Date().toISOString()};
    try{
      const q=JSON.parse(localStorage.getItem("lumiere_events")||"[]");
      q.push(event); localStorage.setItem("lumiere_events",JSON.stringify(q.slice(-200)));
    }catch(e){}
    if(typeof gtag==="function") gtag("event",type,detail);
  };
  document.querySelectorAll(".affiliate-link").forEach(a=>{
    const k=a.dataset.affiliateKey;
    if(c.affiliateLinks&&c.affiliateLinks[k]){
      a.href=c.affiliateLinks[k]; a.rel="sponsored nofollow noopener"; a.target="_blank";
    }
    a.addEventListener("click",()=>log("affiliate_click",{key:k,href:a.href}));
  });
  document.querySelectorAll('a[href*="buy.stripe.com"]').forEach(a=>{
    a.addEventListener("click",()=>log("checkout_click",{label:a.textContent.trim(),href:a.href}));
  });
  document.querySelectorAll('a[href*="lumiereconseilai21.wordpress.com"]').forEach(a=>{
    a.addEventListener("click",()=>log("diagnosis_click",{href:a.href}));
  });
  document.querySelectorAll(".ad-slot").forEach((el,i)=>{
    const key=el.dataset.adSlot||("slot_"+i);
    if(!c.adsenseClient){
      el.innerHTML='<strong>おすすめ</strong><br><a class="btn small" href="./plans.html?utm_source=monetize_hub&utm_medium=house_ad&utm_campaign=plans&utm_content='+encodeURIComponent(key)+'">旅費見直しプランを比較する</a>';
      el.classList.add("house-ad");
    }
  });
  log("page_view",{title:document.title});
})();