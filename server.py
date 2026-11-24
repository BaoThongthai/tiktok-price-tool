import csv,io,json,secrets,sys,threading,time,webbrowser,base64,urllib.request,urllib.error
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path

TOKEN=secrets.token_urlsafe(24)
lock=threading.Lock()
state={'busy':False,'rows':[],'logs':[],'connected':0,'run_id':None}
pending=None
HTML=Path(__file__).with_name('ui.html').read_text(encoding='utf-8')
def shop_document(value=None,sha=None):
    root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
    config_path=root/'settings.private.json'
    config=json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    token=config.get('github_token','')
    headers={'Accept':'application/vnd.github+json','User-Agent':'TikTokPriceTool'}
    if token:headers['Authorization']='Bearer '+token
    endpoint='https://api.github.com/repos/BaoThongthai/tiktok-price-tool/contents/shops.json'
    data=None
    if value is not None:
        if not token:raise RuntimeError('Máy treo chưa có GitHub token để lưu shop.')
        payload={'message':'Update shared shop list','content':base64.b64encode(json.dumps(value,ensure_ascii=False,indent=2).encode()).decode(),'branch':'main'}
        if sha:payload['sha']=sha
        data=json.dumps(payload).encode();headers['Content-Type']='application/json'
    request=urllib.request.Request(endpoint,data=data,headers=headers,method='PUT' if data else 'GET')
    try:
        with urllib.request.urlopen(request,timeout=30) as response:result=json.load(response)
    except urllib.error.HTTPError as e:
        if e.code==404 and value is None:return [],None
        if e.code==409:raise FileExistsError('Danh sách vừa được cập nhật trên thiết bị khác.')
        raise RuntimeError('Không cập nhật được GitHub (HTTP '+str(e.code)+'). Kiểm tra token trên máy treo.') from None
    if value is not None:return value,result.get('content',{}).get('sha')
    shops=json.loads(base64.b64decode(result['content']).decode('utf-8'))
    if not isinstance(shops,list):raise RuntimeError('shops.json trên GitHub không đúng cấu trúc.')
    return shops,result['sha']
def add_shop(name,url):
    if not isinstance(name,str) or not isinstance(url,str):raise ValueError('Nhập tên shop và link TikTok.')
    name=name.strip();url=url.strip();parsed=urlparse(url)
    if not name or len(name)>120:raise ValueError('Tên shop cần có từ 1 đến 120 ký tự.')
    if parsed.scheme!='https' or parsed.hostname not in ('shop.tiktok.com','www.tiktok.com','vt.tiktok.com','vm.tiktok.com') or parsed.username or parsed.password:raise ValueError('Nhập link HTTPS TikTok hợp lệ.')
    for attempt in range(3):
        shops,sha=shop_document()
        if any(s.get('url')==url for s in shops):raise ValueError('Link này đã có trong danh sách shop.')
        new=shops+[{'id':secrets.token_hex(8),'name':name,'url':url}]
        try:return shop_document(new,sha)[0]
        except FileExistsError:
            if attempt==2:raise RuntimeError('Danh sách đang được cập nhật. Hãy bấm lưu lại.')
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,data='',kind='text/plain; charset=utf-8',code=200):
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data.encode('utf-8'))
    def json(self,obj):self.reply(json.dumps(obj,ensure_ascii=False),'application/json; charset=utf-8')
    def valid(self):return self.path.split('?')[0].startswith('/'+TOKEN+'/')
    def do_GET(self):
        global pending
        if not self.valid():return self.reply('Not found',code=404)
        route=self.path.split('?')[0].rsplit('/',1)[-1]
        if route=='state':
            with lock:payload=dict(state,connected=time.time()-state['connected']<8)
            return self.json(payload)
        if route=='shops':
            try:return self.json({'shops':shop_document()[0]})
            except Exception as e:return self.reply(str(e),code=502)
        if route=='bridge-job':
            with lock:
                state['connected']=time.time();job=pending;pending=None
            return self.json({'job':job})
        if route=='bridge-status':
            with lock:payload={'run_id':state['run_id'],'busy':state['busy']}
            return self.json(payload)
        if route=='csv':
            with lock:rows=list(state['rows'])
            buf=io.StringIO();w=csv.writer(buf);w.writerow(['Link sản phẩm','Shop','Tên sản phẩm','Giá trước giảm','Giá sau giảm'])
            for r in rows:w.writerow([r.get('url',''),r['shop'],r['name'],r['before'] if r['before'] is not None else 'Không hiển thị',r['after']])
            self.send_response(200);self.send_header('Content-Type','text/csv; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="Gia_TikTok_'+time.strftime('%Y%m%d_%H%M%S')+'.csv"');self.end_headers();self.wfile.write(('\ufeff'+buf.getvalue()).encode());return
        if route=='':return self.reply(HTML,'text/html; charset=utf-8')
        return self.reply('Not found',code=404)
    def do_POST(self):
        global pending
        if not self.valid():return self.reply('Not found',code=404)
        origin=self.headers.get('Origin','')
        if origin and origin!=f'http://127.0.0.1:{self.server.server_port}' and not origin.startswith('chrome-extension://'):return self.reply('Forbidden',code=403)
        route=self.path.rsplit('/',1)[-1]
        try:
            length=int(self.headers.get('Content-Length',0))
            if length>2000000:raise ValueError()
            body=json.loads(self.rfile.read(length) or b'{}')
        except Exception:return self.reply('Dữ liệu không hợp lệ',code=400)
        if route=='shops':
            try:return self.json({'shops':add_shop(body.get('name'),body.get('url'))})
            except ValueError as e:return self.reply(str(e),code=400)
            except Exception as e:return self.reply(str(e),code=502)
        with lock:
            if route=='stop':
                pending=None;state['busy']=False;state['run_id']=None;state['logs'].append('Đã dừng.');return self.json({'ok':True})
            if route=='run':
                if state['busy']:return self.reply('Tool đang chạy.',code=409)
                if time.time()-state['connected']>8:return self.reply('Chưa kết nối tiện ích. Cài tiện ích vào Chrome cần dùng, rồi tải lại trang tool trong Chrome đó.',code=409)
                links=list(dict.fromkeys(body.get('links','').split()))
                if not links or any(urlparse(x).scheme!='https' or urlparse(x).hostname not in ('shop.tiktok.com','www.tiktok.com','vt.tiktok.com','vm.tiktok.com') for x in links):return self.reply('Nhập link TikTok hợp lệ, mỗi dòng một link.',code=400)
                run_id=secrets.token_hex(12);state.update(busy=True,rows=[],logs=['Đã gửi yêu cầu đến Chrome đang mở.'],run_id=run_id)
                pending={'run_id':run_id,'links':links};return self.json({'ok':True})
            if route=='bridge-result':
                if body.get('run_id')!=state['run_id'] or not state['busy']:return self.json({'ignored':True})
                if body.get('log'):state['logs'].append(str(body['log'])[:1500])
                if body.get('rows'):
                    rows=body['rows']
                    if not isinstance(rows,list) or any(not isinstance(r,dict) or not isinstance(r.get('name'),str) or not isinstance(r.get('shop'),str) or not isinstance(r.get('after'),(int,float)) or (r.get('before') is not None and not isinstance(r['before'],(int,float))) for r in rows):return self.reply('Invalid rows',code=400)
                    state['rows'].extend(dict({k:r[k] for k in ('shop','name','before','after')},url=r.get('url','') if isinstance(r.get('url',''),str) and urlparse(r.get('url','')).scheme=='https' and urlparse(r.get('url','')).hostname in ('shop.tiktok.com','www.tiktok.com','vt.tiktok.com','vm.tiktok.com') and not urlparse(r.get('url','')).username and not urlparse(r.get('url','')).password else '') for r in rows)
                if body.get('done'):state['busy']=False
                return self.json({'ok':True})
        self.reply('Not found',code=404)
if __name__=='__main__':
    if sys.stdout:sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    url=f'http://127.0.0.1:{server.server_port}/{TOKEN}/'
    print('TikTok Price Tool v4 — giữ cửa sổ này mở.\nNếu mở nhầm Chrome, sao chép địa chỉ dưới vào Chrome bạn muốn dùng:\n'+url,flush=True)
    webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
