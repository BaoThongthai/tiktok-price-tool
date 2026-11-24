import importlib.util,json,threading,urllib.request,urllib.error
from pathlib import Path
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).with_name('server.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
server=m.ThreadingHTTPServer(('127.0.0.1',0),m.Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/{m.TOKEN}/'
def get(p):return urllib.request.urlopen(base+p).read()
def post(p,obj):
    req=urllib.request.Request(base+p,json.dumps(obj).encode(),{'Content-Type':'application/json'},method='POST')
    return json.loads(urllib.request.urlopen(req).read())
try:
    assert 'TikTok Price Tool v4' in get('').decode()
    assert b'id="login"' not in get('')
    assert not json.loads(get('state'))['connected']
    try:post('run',{'links':'https://shop.tiktok.com/vn/pdp/1738431839095981283'});raise AssertionError('must reject disconnected')
    except urllib.error.HTTPError as e:assert e.code==409
    assert json.loads(get('bridge-job'))['job'] is None
    assert json.loads(get('state'))['connected']
    post('run',{'links':'https://shop.tiktok.com/vn/pdp/1738431839095981283'})
    job=json.loads(get('bridge-job'))['job'];assert job and len(job['links'])==1
    assert json.loads(get('bridge-job'))['job'] is None
    rows=[{'shop':'TEST','name':'Mì '+str(i),'before':None if i==0 else 200000,'after':100000} for i in range(9)]
    post('bridge-result',{'run_id':job['run_id'],'rows':rows,'done':True})
    assert len(json.loads(get('state'))['rows'])==9
    assert get('csv').decode('utf-8-sig').count('TEST')==9
    post('run',{'links':'https://shop.tiktok.com/vn/pdp/1738431839095981283'})
    post('stop',{})
    assert post('bridge-result',{'run_id':job['run_id'],'rows':rows})['ignored']
    assert not json.loads(get('state'))['rows']
    print('PASS: connection gating, job delivery, nine rows, CSV, cancellation, stale result rejection')
finally:server.shutdown()
