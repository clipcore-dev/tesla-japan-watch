"""Only reviewed Commons photographs; no image generation or paid API."""
import json,re,hashlib,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APPROVED=[('model3','Tesla Model 3.jpg'),('supercharger','Tesla V3 Supercharger photo.jpg'),('modely','2022 Tesla Model Y Long Range AWD Front.jpg')]
ALLOWED={'CC BY-SA 4.0','CC0'}
def get(url):
 return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'TeslaJapanWatch/1.0 (https://github.com/clipcore-dev/tesla-japan-watch)'}),timeout=30).read()
def main():
 target=ROOT/'assets/photos';target.mkdir(parents=True,exist_ok=True)
 old=json.loads((ROOT/'content/images.json').read_text()) if (ROOT/'content/images.json').exists() else []
 out=[]
 for key,title in APPROVED:
  try:
   url='https://commons.wikimedia.org/w/api.php?action=query&format=json&titles=File:'+urllib.parse.quote(title.replace(' ','_'))+'&prop=imageinfo&iiprop=url%7Cextmetadata&iiurlwidth=960'
   info=next(iter(json.loads(get(url))['query']['pages'].values()))['imageinfo'][0];meta=info['extmetadata']
   license=meta['LicenseShortName']['value']
   if license not in ALLOWED:raise ValueError('License needs editorial review')
   src=info.get('thumburl',info['url'])
   previous=next((x for x in old if x['id']==key),None)
   local=target/(key+'.jpg')
   data=local.read_bytes() if local.exists() else get(src)
   if len(data)>500_000:raise ValueError('Image requires size review; keep existing compressed asset')
   if len(data)>8_000_000 or not data.startswith(b'\xff\xd8'):raise ValueError('Invalid or oversized JPEG')
   (target/(key+'.jpg')).write_bytes(data)
   out.append({'id':key,'path':'assets/photos/'+key+'.jpg','title':title,'author':re.sub('<[^>]+>','',meta['Artist']['value']),'license':license,'licenseUrl':meta.get('LicenseUrl',{}).get('value','https://creativecommons.org/publicdomain/zero/1.0/'),'source':info['descriptionurl'],'changes':'縮小版。表示枠に合わせたトリミングあり。','sha256':hashlib.sha256(data).hexdigest(),'caption':{'model3':'Model 3（2018年撮影・海外参考写真。日本仕様やHWを示すものではありません）','modely':'Model Y（2022年・英国撮影。日本仕様やHWを示すものではありません）','supercharger':'V3 Supercharger（参考写真。日本の新設拠点を撮影したものではありません）'}[key]})
   print(key,'verified')
  except Exception as e:
   previous=next((x for x in old if x['id']==key),None)
   if not previous:raise
   print(key,'retained previous licensed asset:',type(e).__name__);out.append(previous)
 (ROOT/'content/images.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
