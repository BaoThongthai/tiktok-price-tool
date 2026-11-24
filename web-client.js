let base='',authorization='',timer=null;
const el=id=>document.getElementById(id);
async function connection(){
 const r=await fetch('https://raw.githubusercontent.com/BaoThongthai/tiktok-price-tool/main/connection.json?t='+Date.now(),{cache:'no-store'});
 if(!r.ok)throw Error('Máy treo chưa đăng ký kết nối. Hãy chạy ứng dụng server trên máy treo trước.');
 const c=await r.json();
 if(!c.base)throw Error('Máy treo chưa đăng ký kết nối. Hãy chạy TikTokPriceServer.exe trước.');
 const u=new URL(c.base);
 if(u.protocol!=='https:'||u.username||u.password||!/^[-a-z0-9]+\.trycloudflare\.com$/.test(u.hostname))throw Error('Kết nối máy treo không hợp lệ.');
 base=u.href.endsWith('/')?u.href:u.href+'/';
}
async function api(route,body){
 const options={headers:{Authorization:authorization},cache:'no-store'};
 if(body!==undefined){options.method='POST';options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
 let r;
 try{r=await fetch(base+route,options);}catch{throw Error('Không kết nối được máy treo. Kiểm tra ứng dụng server và mạng trên máy treo, rồi đăng nhập lại.');}
 if(r.status===401)throw Error('Sai tài khoản/mật khẩu hoặc máy treo vừa khởi động lại.');
 if(!r.ok)throw Error((await r.text()).slice(0,300)||'Máy treo chưa sẵn sàng.');
 return r;
}
const money=n=>n===null?'Không hiển thị':Number(n).toLocaleString('vi-VN')+'đ';
async function refresh(){
 const s=await(await api('state')).json();
 el('status').textContent=(s.connected?'Chrome: Đã kết nối':'Chrome: Chưa kết nối — mở tab nội bộ trên máy treo')+' • '+(s.busy?'Đang chạy':'Sẵn sàng')+' • '+s.rows.length+' sản phẩm';
 el('run').disabled=s.busy;el('logs').textContent=s.logs.join('\n');el('rows').replaceChildren();
 for(const r of s.rows){const tr=document.createElement('tr');for(const v of [r.shop,r.name,money(r.before),money(r.after)]){const td=document.createElement('td');td.textContent=v;tr.append(td);}el('rows').append(tr);}
}
async function poll(){try{await refresh();}catch(e){el('status').textContent=e.message;}timer=setTimeout(poll,1500);}
el('login-form').onsubmit=async e=>{
 e.preventDefault();el('signin').disabled=true;el('login-status').textContent='Đang kết nối máy treo…';
 try{
  await connection();const raw=new TextEncoder().encode(el('username').value+':'+el('password').value);
  authorization='Basic '+btoa(String.fromCharCode(...raw));
  await refresh();el('password').value='';el('login').hidden=true;el('app').hidden=false;clearTimeout(timer);poll();
 }catch(e){authorization='';el('login-status').textContent=e.message;}
 finally{el('signin').disabled=false;}
};
el('logout').onclick=()=>{authorization='';clearTimeout(timer);el('app').hidden=true;el('login').hidden=false;el('login-status').textContent='Đã đăng xuất.';};
for(const id of ['run','stop'])el(id).onclick=async()=>{try{await api(id,{links:el('links').value});await refresh();}catch(e){el('status').textContent=e.message;}};
el('file').onchange=async e=>{if(e.target.files[0])el('links').value=await e.target.files[0].text();};
el('csv').onclick=async()=>{try{const blob=await(await api('csv')).blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='Gia_TikTok_'+new Date().toISOString().slice(0,10)+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}catch(e){el('status').textContent=e.message;}};
