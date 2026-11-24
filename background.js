importScripts('scanner.js');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let running=false;
chrome.runtime.onMessage.addListener((msg,sender,reply)=>{
  if(msg.type!=='tp-tick'||!sender.tab||!sender.url)return;
  const u=new URL(sender.url);
  if(u.hostname!=='127.0.0.1'||msg.base!==u.origin+u.pathname||!/^\/[\w-]{20,}\/$/.test(u.pathname))return;
  (async()=>{
    const response=await fetch(msg.base+'bridge-job',{cache:'no-store'});
    const {job}=await response.json();
    if(job){
      if(running){await report(msg.base,job.run_id,{log:'Chrome đang xử lý một phiên khác. Đợi hoàn tất rồi bấm lại.',done:true});}
      else{running=true;run(msg.base,job,sender.tab.windowId).finally(()=>running=false);}
    }
    reply({ok:true});
  })().catch(e=>reply({error:e.message}));
  return true;
});
async function report(base,id,payload){await fetch(base+'bridge-result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:id,...payload})});}
async function active(base,id){const r=await(await fetch(base+'bridge-status',{cache:'no-store'})).json();return r.busy&&r.run_id===id;}
async function readStable(base,id,tabId,func,args=[]){
  const deadline=Date.now()+180000;let signature='',stable=0,result=null,notice=false;
  while(Date.now()<deadline){
    await sleep(1000);
    if(!await active(base,id))throw Error('Đã dừng.');
    const current=await chrome.tabs.get(tabId);
    if(current.status!=='complete')continue;
    let values;
    try{values=await chrome.scripting.executeScript({target:{tabId},func,args});}catch{continue;}
    const data=values[0]?.result;
    if(data?.error)throw Error(data.error);
    if(data&&(data.rows?.length||data.after>0)){
      const sig=JSON.stringify(data);stable=sig===signature?stable+1:0;signature=sig;result=data;
      if(stable>=4)return result;
    }else{
      stable=0;
      if(!notice&&/security check|captcha|verify/i.test(current.title||'')){
        notice=true;await report(base,id,{log:'TikTok yêu cầu xác minh trong tab vừa mở. Hãy hoàn tất thủ công; tool chờ tối đa 3 phút.'});
      }
    }
  }
  throw Error('Không đọc được dữ liệu trong 3 phút. Kiểm tra tab TikTok, đăng nhập/xác minh nếu có rồi chạy lại.');
}
async function run(base,job,windowId){
  let tabId;
  try{
    const tab=await chrome.tabs.create({url:'about:blank',windowId,active:true});tabId=tab.id;
    for(let i=0;i<job.links.length;i++){
      if(!await active(base,job.run_id))break;
      const link=job.links[i];
      await report(base,job.run_id,{log:`[${i+1}/${job.links.length}] Đang mở ${link}`});
      try{
        await chrome.tabs.update(tabId,{url:link,active:true});
        const result=await readStable(base,job.run_id,tabId,scanPage);
        const shop=result.heading.replace(/^(Khám phá thêm sản phẩm từ|Explore more from|Discover more from)\s*/i,'').trim();
        await report(base,job.run_id,{log:`${shop}: tìm thấy ${result.rows.length} link, đang mở từng trang để lấy giá mặc định.`});
        for(let j=0;j<result.rows.length;j++){
          if(!await active(base,job.run_id))return;
          const product=result.rows[j];
          try{
            await report(base,job.run_id,{log:`[SP ${j+1}/${result.rows.length}] Đọc trang chi tiết: ${product.name}`});
            await chrome.tabs.update(tabId,{url:product.url,active:true});
            const detail=await readStable(base,job.run_id,tabId,scanDetail,[product.url]);
            await report(base,job.run_id,{rows:[{...detail,shop}],log:`Đã lấy giá trong trang: ${detail.after.toLocaleString('vi-VN')}đ`});
          }catch(e){
            if(!await active(base,job.run_id))return;
            await report(base,job.run_id,{log:`LỖI SP ${product.url}: ${e.message}. Không dùng giá ở thẻ bên ngoài.`});
          }
        }
      }catch(e){await report(base,job.run_id,{log:`LỖI ${link}: ${e.message}`});}
    }
    await report(base,job.run_id,{done:true,log:'Hoàn tất. Quay lại tab tool để xem bảng và xuất CSV.'});
  }catch(e){try{await report(base,job.run_id,{done:true,log:'Lỗi kết nối Chrome: '+e.message});}catch{}}
  // Keep the TikTok tab open so the user can inspect the page or verification.
}
