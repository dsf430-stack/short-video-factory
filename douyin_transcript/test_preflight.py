import importlib.util,json,pathlib,tempfile,types,unittest,hashlib,subprocess,shutil
spec=importlib.util.spec_from_file_location('adapter',pathlib.Path(__file__).with_name('run.py')); a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class Checks(unittest.TestCase):
 def exercise(self,payload,fail):
  with tempfile.TemporaryDirectory() as folder:
   text='window._ROUTER_DATA = '+json.dumps(payload)+'</script>'
   response=types.SimpleNamespace(url='https://www.iesdouyin.com/share/video/123/?share_sign=DO_NOT_LEAK',status_code=200,content=text.encode(),text=text)
   original=lambda *args,**kwargs:response
   req=types.SimpleNamespace(get=original)
   def parse(link):
    req.get(link)
    if fail: raise ValueError('视频信息为空')
    return {'video_id':'123','video_url':'https://example.com/video.mp4'}
   dt=types.SimpleNamespace(requests=req,get_video_info=parse)
   out=pathlib.Path(folder)
   if fail:
    with self.assertRaisesRegex(RuntimeError,'SHARE_PAGE_HAS_NO_MEDIA_DATA'): a.get_info(dt,'link',out)
   else: self.assertEqual(a.get_info(dt,'link',out)['video_id'],'123')
   self.assertIs(req.get,original)
   raw=(out/'link-diagnostic.json').read_text(); self.assertNotIn('DO_NOT_LEAK',raw)
   d=json.loads(raw); self.assertEqual(d['status'],'FAIL' if fail else 'PASS')
 def test_real_missing_data_shape(self):
  self.exercise({'loaderData':{'video_layout':None,'video_(id)/page':{'itemId':'123','renderInSSR':1,'abParams':{}}}},True)
 def test_usable_data_preserved(self):
  self.exercise({'loaderData':{'video_(id)/page':{'itemId':'123','videoInfoRes':{'item_list':[{'video':{}}]}}}},False)
if __name__ == '__main__':
 unittest.main()
