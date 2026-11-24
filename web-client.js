let base='',authorization='',timer=null;
let shops=[];
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
  await refresh();el('password').value='';el('login').hidden=true;el('app').hidden=false;clearTimeout(timer);poll();loadShops();
 }catch(e){authorization='';el('login-status').textContent=e.message;}
 finally{el('signin').disabled=false;}
};
el('logout').onclick=()=>{authorization='';clearTimeout(timer);el('app').hidden=true;el('login').hidden=false;el('login-status').textContent='Đã đăng xuất.';};
for(const id of ['run','stop'])el(id).onclick=async()=>{try{await api(id,{links:el('links').value});await refresh();}catch(e){el('status').textContent=e.message;}};
el('file').onchange=async e=>{if(e.target.files[0])el('links').value=await e.target.files[0].text();};
el('csv').onclick=async()=>{try{const blob=await(await api('csv')).blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='Gia_TikTok_'+new Date().toISOString().slice(0,10)+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}catch(e){el('status').textContent=e.message;}};
function renderShops(){
 const selected=new Set([...el('shop-list').querySelectorAll('input:checked')].map(e=>e.value));
 el('shop-list').replaceChildren();
 for(const shop of shops){
  const row=document.createElement('label');row.className='shop-row';
  const check=document.createElement('input');check.type='checkbox';check.value=shop.id;check.checked=selected.size?selected.has(shop.id):true;
  const text=document.createElement('span');text.textContent=shop.name;
  const small=document.createElement('small');small.textContent=shop.url;text.append(document.createElement('br'),small);row.append(check,text);el('shop-list').append(row);
 }
 if(!shops.length)el('shop-list').textContent='Chưa có shop. Bấm Thêm shop để tạo.';
}
async function loadShops(){
 try{const data=await(await api('shops')).json();shops=data.shops;renderShops();el('shop-message').textContent=shops.length+' shop · lưu chung trên GitHub';}
 catch(e){el('shop-message').textContent=e.message.includes('Not found')?'Cần cập nhật TikTokPriceServer.exe trên máy treo để dùng danh sách shop.':e.message;}
}
el('add-shop').onclick=()=>{el('shop-form').reset();el('shop-error').textContent='';el('shop-dialog').showModal();el('shop-name').focus();};
el('cancel-shop').onclick=()=>el('shop-dialog').close();
el('reload-shops').onclick=loadShops;
el('shop-form').onsubmit=async e=>{
 e.preventDefault();el('save-shop').disabled=true;el('shop-error').textContent='Đang lưu lên GitHub…';
 try{
  const data=await(await api('shops',{name:el('shop-name').value.trim(),url:el('shop-url').value.trim()})).json();
  shops=data.shops;renderShops();el('shop-dialog').close();el('shop-message').textContent='Đã lưu shop lên GitHub · '+shops.length+' shop';
 }catch(e){el('shop-error').textContent=e.message;}
 finally{el('save-shop').disabled=false;}
};
el('run-shops').onclick=()=>{
 const selected=new Set([...el('shop-list').querySelectorAll('input:checked')].map(e=>e.value));
 const links=shops.filter(s=>selected.has(s.id)).map(s=>s.url);
 if(!links.length){el('shop-message').textContent='Chọn ít nhất một shop để lấy giá.';return;}
 el('links').value=links.join('\n');el('run').click();
};
