function scanPage() { try {
 const s=document.getElementById('pdp-discover-more-section');
 if(!s){window.scrollBy(0,800);return null;}
 s.scrollIntoView({block:'center'});
 const heading=[...s.querySelectorAll('span,h2,h3')].map(e=>e.textContent.trim()).find(t=>/^(Khám phá thêm sản phẩm từ|Explore more from|Discover more from)/i.test(t))||'';
 if(!/^(Khám phá thêm sản phẩm từ|Explore more from|Discover more from)/i.test(heading)) return null;
 const seen=new Set();
 const rows=[...s.querySelectorAll('h3')].map(h=>{
   const c=h.closest('[class*="horizontalItem-"]');
   if(!c) throw Error('TikTok đã đổi cấu trúc thẻ sản phẩm');
   const link=h.closest('a')?.href;
   if(!link||seen.has(link)) return null;
   seen.add(link);
   return {name:(h.title||h.textContent).trim(),url:link};
 }).filter(Boolean);
 return {heading,rows};
} catch(e){return {error:e.message};} }

function scanDetail(expectedUrl) {
 try {
   const id=new URL(expectedUrl).pathname.match(/\d{15,}/)?.[0];
   if(id&&!location.pathname.includes(id))return null;
   const h=document.querySelector('h1');
   if(!h)return null;
   const info=h.parentElement;
   const price=info.querySelector('.Headline-Semibold');
   if(!price)return null;
   const raw=price.textContent.trim();
   // An unresolved range is not a price for a selected default variant.
   if(!/^[\d.,\s₫đ]+$/.test(raw))return {error:'Trang đang hiển thị khoảng giá, chưa xác định được giá mặc định: '+raw};
   const after=Number(raw.replace(/[^0-9]/g,''));
   if(!after)return null;
   const old=info.querySelector('.line-through,del,s');
   const before=old?Number(old.textContent.replace(/[^0-9]/g,'')):null;
   if(old&&!before)return {error:'Không đọc được giá trước giảm trong trang chi tiết.'};
   return {name:h.textContent.trim(),before,after};
 } catch(e){return {error:e.message};}
}
