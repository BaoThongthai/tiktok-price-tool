import base64,hashlib,threading,urllib.request,urllib.error
import public_server as p
app=p.app
auth='Basic '+base64.b64encode(b'admin:test-password-123').decode()
p.PublicHandler.auth_hash=hashlib.sha256(auth.encode()).digest()
srv=app.ThreadingHTTPServer(('127.0.0.1',0),p.PublicHandler)
threading.Thread(target=srv.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{srv.server_port}/{app.TOKEN}/'
def request(route,headers=None,data=None):return urllib.request.urlopen(urllib.request.Request(base+route,data,headers or {}))
try:
    for route,headers,code in [('state',{},401),('bridge-job',{},404),('bridge-job',{'Authorization':auth},404),('bridge-status',{'Authorization':auth},404)]:
        try:request(route,headers);raise AssertionError('must reject')
        except urllib.error.HTTPError as e:assert e.code==code
    assert request('',{'Authorization':auth}).status==200
    assert request('state',{'Authorization':auth}).status==200
    try:request('stop',{'Authorization':auth,'Origin':'https://evil.example'},b'{}');raise AssertionError('must reject origin')
    except urllib.error.HTTPError as e:assert e.code==403
    assert request('stop',{'Authorization':auth,'Origin':f'https://127.0.0.1:{srv.server_port}'},b'{}').status==200
    print('PASS: public authentication, bridge isolation, same-origin controls')
finally:srv.shutdown()
