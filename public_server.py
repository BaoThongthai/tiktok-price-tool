"""Public HTTPS access through Cloudflare; Chrome bridge remains loopback-only."""
import base64,getpass,hashlib,hmac,os,re,subprocess,sys,threading,urllib.request,webbrowser
from pathlib import Path
from urllib.parse import urlparse
import server as app

class PublicHandler(app.Handler):
    auth_hash=None
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
            if u.scheme!='https' or u.netloc!=self.headers.get('Host'):
                return self.reply('Forbidden',code=403)
        # Base handler independently enforces the per-session URL token.
        # The remote origin was checked above; normalize it for its local-only guard.
        if 'Origin' in self.headers:del self.headers['Origin']
        self.headers['Origin']=f'http://127.0.0.1:{self.server.server_port}'
        super().do_POST()

def main():
    if sys.stdout:sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    print('TikTok Price Tool — Truy cập Internet\nTài khoản đăng nhập: admin\nMật khẩu chỉ giữ trong bộ nhớ của lần chạy, không đưa lên GitHub.')
    while True:
        password=getpass.getpass('Đặt mật khẩu truy cập (tối thiểu 10 ký tự): ')
        if len(password)<10:print('Mật khẩu cần ít nhất 10 ký tự.');continue
        if password!=getpass.getpass('Nhập lại mật khẩu: '):print('Hai mật khẩu khác nhau.');continue
        break
    auth='Basic '+base64.b64encode(('admin:'+password).encode('utf-8')).decode('ascii')
    PublicHandler.auth_hash=hashlib.sha256(auth.encode()).digest()
    del password,auth
    local=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
    public=app.ThreadingHTTPServer(('127.0.0.1',0),PublicHandler)
    threading.Thread(target=local.serve_forever,daemon=True).start()
    threading.Thread(target=public.serve_forever,daemon=True).start()
    local_url=f'http://127.0.0.1:{local.server_port}/{app.TOKEN}/'
    print('\nMở địa chỉ này trong Chrome đã cài tiện ích và giữ tab đó mở:\n'+local_url,flush=True)
    webbrowser.open(local_url)
    root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
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
                (root/'LINK_PUBLIC.txt').write_text(link+'\nTài khoản: admin\nMật khẩu: mật khẩu bạn vừa đặt.\n',encoding='utf-8')
                print('\nLINK TRUY CẬP INTERNET:\n'+link+'\nTài khoản: admin. Dùng mật khẩu bạn vừa đặt.\nLink cũng được lưu trong LINK_PUBLIC.txt.\nGiữ ứng dụng và tab Chrome nội bộ mở để xử lý công việc.\n',flush=True)
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
