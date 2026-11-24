import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('app',Path(__file__).with_name('server.py'))
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
stored=[];writes=[];conflict=True
def fake(value=None,sha=None):
    global stored,conflict
    if value is None:return list(stored),'revision'
    if conflict:
        conflict=False
        stored=[{'id':'other','name':'Shop khác','url':'https://shop.tiktok.com/vn/pdp/1'}]
        raise FileExistsError()
    stored=value;writes.append(value);return value,'new'
app.shop_document=fake
result=app.add_shop(' Thiên Phước ','https://shop.tiktok.com/vn/pdp/1738431839095981283')
assert len(result)==2 and result[0]['id']=='other' and result[1]['name']=='Thiên Phước'
assert len(writes)==1
for name,url in [('',result[1]['url']),('Trùng',result[1]['url']),('Sai','https://evil.example/'),('Sai','https://user:password@shop.tiktok.com/a')]:
    try:app.add_shop(name,url);raise AssertionError('must reject')
    except ValueError:pass
print('PASS: GitHub shop creation, name trimming, duplicates, valid URLs, concurrent update preservation')
