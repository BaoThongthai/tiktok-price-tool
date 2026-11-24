const fs=require('fs'),vm=require('vm'),assert=require('assert');
function fixture(price='161.499',old='389.000₫',path='/vn/pdp/1738431839094342883'){
 const h={textContent:'Phở Bò',parentElement:{querySelector:s=>s==='.Headline-Semibold'?{textContent:price}:old?{textContent:old}:null}};
 const c={document:{querySelector:s=>s==='h1'?h:null},location:{pathname:path},URL};
 vm.createContext(c);vm.runInContext(fs.readFileSync(__dirname+'/scanner.js','utf8'),c);return c;
}
const url='https://shop.tiktok.com/vn/pdp/1738431839094342883';
assert.equal(fixture().scanDetail(url).after,161499);
assert.equal(fixture().scanDetail(url).before,389000);
assert.equal(fixture('288.100',null).scanDetail(url).before,null);
assert(fixture('100.000 - 200.000').scanDetail(url).error);
assert.equal(fixture('100.000',null,'/vn/pdp/1738431839094998243').scanDetail(url),null);
// Verify the orchestration reads every discovered URL and emits only detail prices.
(async()=>{
 let urlNow='',emitted=[],opened=[];
 const rows=Array.from({length:9},(_,i)=>({name:'P'+i,url:'https://shop.tiktok.com/vn/pdp/'+i}));
 const c={importScripts(){},setTimeout:fn=>fn(),URL,Date,console,
 chrome:{runtime:{onMessage:{addListener(){}}},tabs:{create:async()=>({id:1}),update:async(id,o)=>{urlNow=o.url;opened.push(o.url)},get:async()=>({status:'complete'})},scripting:{executeScript:async({func,args})=>[{result:func.name==='scanPage'?{heading:'Explore more from TEST',rows}:{name:'DETAIL',before:200000,after:123000}}]}},
 fetch:async(path,opts)=>{if(opts?.body)emitted.push(JSON.parse(opts.body));return {json:async()=>path.endsWith('bridge-status')?{busy:true,run_id:'R'}:{}};},
 scanPage:function scanPage(){},scanDetail:function scanDetail(){}};
 vm.createContext(c);vm.runInContext(fs.readFileSync(__dirname+'/background.js','utf8'),c);
 await c.run('http://127.0.0.1/','R'===null?null:{run_id:'R',links:['https://shop.tiktok.com/vn/pdp/source']},1);
 assert.equal(opened.length,10,JSON.stringify(emitted));
 const actual=emitted.flatMap(x=>x.rows||[]);assert.equal(actual.length,9);assert(actual.every(r=>r.after===123000&&r.name==='DETAIL'));
 console.log('PASS: detail prices, missing original price, range rejection, stale-page guard, nine sequential detail visits');
})().catch(e=>{console.error(e);process.exitCode=1});
