(() => {
  if(document.title!=='TikTok Price Tool v4'||!/^\/[\w-]{20,}\/$/.test(location.pathname))return;
  const tick=()=>chrome.runtime.sendMessage({type:'tp-tick',base:location.origin+location.pathname}).catch(()=>{});
  tick();setInterval(tick,1000);
})();
