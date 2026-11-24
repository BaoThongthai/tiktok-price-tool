"""Public HTTPS access through Cloudflare; Chrome bridge remains loopback-only."""
import base64,getpass,hashlib,hmac,os,re,subprocess,sys,threading,urllib.request,webbrowser
from pathlib import Path
from urllib.parse import urlparse
import server as app

class PublicHandler(app.Handler):
    auth_hash=None
    pages_origin='https://baothongthai.github.io'
    def end_headers(self):
        if self.headers.get('Origin')==self.pages_origin:
            self.send_header('Access-Control-Allow-Origin',self.pages_origin)
            self.send_header('Vary','Origin')
        super().end_headers()
    def do_OPTIONS(self):
        if self.headers.get('Origin')!=self.pages_origin:return self.reply('Forbidden',code=403)
        self.send_response(204)
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type')
        self.send_header('Access-Control-Max-Age','600')
        self.end_headers()
    def authorized(self):
        actual=hashlib.sha256(self.headers.get('Authorization','').encode()).digest()
        if self.auth_hash and hmac.compare_digest(actual,self.auth_hash):return True
        self.send_response(401);self.send_header('WWW-Authenticate','Basic realm="TikTok Price Tool", charset="UTF-8"');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b'Login required');return False
    def blocked(self):
        route=self.path.split('?')[0].rsplit('/',1)[-1]
        if route.startswith('bridge-'):
            self.reply('Not found',code=404);return True
        return False
    def do_GET(self):
        if self.blocked() or not self.authorized():return
        if self.path=='/':
            self.send_response(302);self.send_header('Location','/'+app.TOKEN+'/');self.end_headers();return
        super().do_GET()
    def do_POST(self):
        if self.blocked() or not self.authorized():return
        origin=self.headers.get('Origin','')
        if origin:
            u=urlparse(origin)
            if origin!=self.pages_origin and (u.scheme!='https' or u.netloc!=self.headers.get('Host')):
                return self.reply('Forbidden',code=403)
        # Base handler independently enforces the per-session URL token.
        # The remote origin was checked above; normalize it for its local-only guard.
        if 'Origin' in self.headers:del self.headers['Origin']
        self.headers['Origin']=f'http://127.0.0.1:{self.server.server_port}'
        super().do_POST()

def publish_connection(base_url,github_token,repository='BaoThongthai/tiktok-price-tool'):
    import json,datetime,urllib.error
    endpoint='https://api.github.com/repos/'+repository+'/contents/connection.json'
    headers={'Authorization':'Bearer '+github_token,'Accept':'application/vnd.github+json','User-Agent':'TikTokPriceTool','X-GitHub-Api-Version':'2022-11-28'}
    # Use the stable documented media type; API version remains optional.
    headers.pop('X-GitHub-Api-Version')
    sha=None
    try:
        with urllib.request.urlopen(urllib.request.Request(endpoint,headers=headers),timeout=30) as r:sha=json.load(r)['sha']
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
    content=json.dumps({'base':base_url,'updated':datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False)
    payload={'message':'Update machine connection','content':base64.b64encode(content.encode()).decode(),'branch':'main'}
    if sha:payload['sha']=sha
    with urllib.request.urlopen(urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={**headers,'Content-Type':'application/json'},method='PUT'),timeout=30) as r:
        if r.status not in (200,201):raise RuntimeError('Không cập nhật được kết nối GitHub.')

def main():
    import json
    if sys.stdout:sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
    config_path=root/'settings.private.json'
    print('TikTok Price Tool — Server cho GitHub Pages\nTài khoản đăng nhập: admin\nCấu hình riêng chỉ lưu trên máy, không đưa lên GitHub.')
    config=json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    if not config.get('auth_hash'):
        while True:
            password=getpass.getpass('Đặt mật khẩu đăng nhập website: ')
            if not password:continue
            if password!=getpass.getpass('Nhập lại mật khẩu: '):print('Hai mật khẩu khác nhau.');continue
            break
        auth='Basic '+base64.b64encode(('admin:'+password).encode('utf-8')).decode('ascii')
        config['auth_hash']=hashlib.sha256(auth.encode()).hexdigest()
        del password,auth
    if not config.get('github_token'):
        print('Lần đầu cần GitHub Fine-grained token, chỉ chọn repository tiktok-price-tool và quyền Contents: Read and write. Dán token ở đây, không gửi token qua chat.')
        config['github_token']=getpass.getpass('GitHub token: ').strip()
        if not config['github_token']:raise RuntimeError('Chưa nhập GitHub token.')
    config_path.write_text(json.dumps(config,indent=2),encoding='utf-8')
    PublicHandler.auth_hash=bytes.fromhex(config['auth_hash'])
    local=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
    public=app.ThreadingHTTPServer(('127.0.0.1',0),PublicHandler)
    threading.Thread(target=local.serve_forever,daemon=True).start()
    threading.Thread(target=public.serve_forever,daemon=True).start()
    local_url=f'http://127.0.0.1:{local.server_port}/{app.TOKEN}/'
    print('\nMở địa chỉ này trong Chrome đã cài tiện ích và giữ tab đó mở:\n'+local_url,flush=True)
    webbrowser.open(local_url)
    binary=root/'cloudflared.exe'
    if not binary.exists():
        print('\nĐang tải cloudflared từ kho chính thức Cloudflare…',flush=True)
        try:
            urllib.request.urlretrieve('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe',binary)
        except Exception:
            if binary.exists():binary.unlink()
            raise
    proc=subprocess.Popen([str(binary),'tunnel','--url',f'http://127.0.0.1:{public.server_port}'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),text=True,encoding='utf-8',errors='replace')
    try:
        found=False
        for line in proc.stdout:
            match=re.search(r'https://[a-z0-9-]+\.trycloudflare\.com',line)
            if match and not found:
                found=True
                link=match.group(0)+'/'+app.TOKEN+'/'
                print('Đang tự cập nhật kết nối cho link GitHub Pages…',flush=True)
                publish_connection(link,config['github_token'])
                (root/'LINK_PUBLIC.txt').write_text(link+'\nTài khoản: admin\nMật khẩu: mật khẩu bạn vừa đặt.\n',encoding='utf-8')
                print('\nLINK CỐ ĐỊNH:\nhttps://baothongthai.github.io/tiktok-price-tool/\nTài khoản: admin. Dùng mật khẩu đã cấu hình.\nKết nối có thể cần khoảng một phút để cập nhật.\nGiữ ứng dụng và tab Chrome nội bộ mở để xử lý công việc.\n',flush=True)
            elif 'ERR' in line or 'error' in line.lower():print(line.strip(),flush=True)
        if not found:raise RuntimeError('Chưa tạo được link tunnel. Kiểm tra mạng rồi mở lại ứng dụng.')
    finally:
        proc.terminate();local.shutdown();public.shutdown()

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
    except Exception as e:
        print('Lỗi: '+str(e),flush=True)
        input('Nhấn Enter để đóng…')
