"""Free unauthenticated HTTP/RSS/JSON-LD collection. Remote text is data only."""
import concurrent.futures,datetime as dt,hashlib,html,json,re,urllib.request,urllib.parse,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TZ=dt.timezone(dt.timedelta(hours=9))
SOURCES=[
 ('tesla-jp','Tesla Japan 公式発表','https://prtimes.jp/companyrdf.php?company_id=38481','rss','日本公式'),
 ('world','世界FSD報道の発見用RSS','https://news.google.com/rss/search?q=Tesla+%22FSD%22+when:1d&hl=en-US&gl=US&ceid=US:en','rss','海外報道・未検証'),
 ('fsd-jp','FSD 世界提供地域（Tesla公式）','https://www.tesla.com/ja_jp/fsd/safety','page','FSD・規制'),
 ('fsd-us','FSD 米国価格・機能（Tesla公式）','https://www.tesla.com/support/fsd','page','FSD・価格'),
 ('rdw','オランダRDW：FSD承認の公式説明','https://www.rdw.nl/en/news/2026/rdw-explanation-of-european-type-approval-tesla-with-provisional-validity-in-the-netherlands','page','欧州規制'),
 ('authorities','規制当局の関連発表（RSS発見）','https://news.google.com/rss/search?q=(site:rdw.nl+OR+site:nhtsa.gov+OR+site:mlit.go.jp)+Tesla+when:30d&hl=en-US&gl=US&ceid=US:en','rss','規制当局・原文確認'),
 ('regulator','米国NHTSA TeslaリコールAPI / Model Y 2026','https://api.nhtsa.gov/recalls/recallsByVehicle?make=TESLA&model=MODEL%20Y&modelYear=2026','recalls','米国規制'),
 ('stations','日本Supercharger公式一覧','https://www.tesla.com/ja_jp/findus/list/superchargers/Japan','stations','新設・掲載'),
 ('mobile','モバイルコネクター公式商品','https://shop.tesla.com/ja_jp/product/mobile-connector','product','充電・在庫'),
 ('wall','ウォールコネクター公式商品','https://shop.tesla.com/ja_jp/product/wall-connector','product','充電・在庫'),
 ('chademo','CHAdeMO公式商品（URL存続も確認）','https://shop.tesla.com/ja_jp/product/chademo-adapter','product','充電・在庫'),
 ('charging','日本公式ショップ充電カテゴリ','https://shop.tesla.com/ja_jp/category/charging','page','充電・販売')]
def safe_url(url):
 p=urllib.parse.urlparse(url)
 return url if p.scheme=='https' and p.hostname else ''
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ('script','style','noscript'):self.skip+=1
 def handle_endtag(self,t):
  if t in ('script','style','noscript'):self.skip=max(0,self.skip-1)
 def handle_data(self,s):
  if not self.skip:self.parts.append(s)
def plain(s):
 p=Text();p.feed(s);return re.sub(r'\s+',' ',' '.join(p.parts)).strip()
def request(url):
 req=urllib.request.Request(url,headers={'User-Agent':'TeslaJapanWatch/1.0 (+https://github.com/clipcore-dev/tesla-japan-watch)','Accept':'text/html,application/json,application/rss+xml,application/xml'})
 with urllib.request.urlopen(req,timeout=22) as r:
  b=r.read(3_000_001)
  if len(b)>3_000_000:raise ValueError('Response exceeds cap')
  return b.decode('utf-8','replace')
def items_from_rss(raw):
 root=ET.fromstring(raw);out=[]
 for node in root.iter():
  if node.tag.split('}')[-1] not in ('item','entry'):continue
  fields={c.tag.split('}')[-1]:c for c in node}
  val=lambda k: ''.join(fields[k].itertext()).strip() if k in fields else ''
  link=val('link') or (fields['link'].attrib.get('href','') if 'link' in fields else '')
  full_title=plain(val('title'));title=full_title[:99]+'…' if len(full_title)>100 else full_title
  if safe_url(link) and title:out.append({'title':title,'url':link,'published':val('pubDate') or val('date') or val('published')})
 return out[:30]
def offers(raw):
 found=[]
 def walk(x):
  if isinstance(x,list):
   for y in x:walk(y)
  elif isinstance(x,dict):
   types=x.get('@type',[]);types=[types] if isinstance(types,str) else types
   if 'Offer' in types:
    a=x.get('availability','').split('/')[-1]
    if a in ('InStock','OutOfStock','PreOrder','BackOrder','SoldOut'):found.append({'availability':a,'price':str(x.get('price',''))[:20],'currency':str(x.get('priceCurrency',''))[:6]})
   for y in x.values():
    if isinstance(y,(dict,list)):walk(y)
 for block in re.findall(r'<script[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>',raw,re.S|re.I):
  try:walk(json.loads(block))
  except (ValueError,TypeError):pass
 return found[:10]
def stations(raw):
 out={}
 for url,label in re.findall(r'<a\b[^>]*href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>',raw,re.S|re.I):
  url=urllib.parse.urljoin('https://www.tesla.com',html.unescape(url))
  if '/findus/location/supercharger/' in url and safe_url(url):out[url]={'name':plain(label)[:100],'url':url}
 if len(out)<20:raise ValueError('Station schema missing; do not treat as removal')
 return sorted(out.values(),key=lambda x:x['url'])
def collect(src):
 key,name,url,kind,topic=src
 try:
  raw=request(url)
  if re.search(r'Access Denied|captcha|verify you are human',raw,re.I):raise ValueError('Access restricted')
  value={'id':key,'name':name,'url':url,'topic':topic,'ok':True,'checkedAt':NOW}
  if kind=='rss':value['items']=items_from_rss(raw)
  elif kind=='stations':value['stations']=stations(raw)
  elif kind=='recalls':
   x=json.loads(raw)
   if 'results' not in x:raise ValueError('Recall schema missing')
   value['recalls']=[{'id':r.get('NHTSACampaignNumber'),'component':r.get('Component'),'reported':r.get('ReportReceivedDate')} for r in x['results']][:100]
  elif kind=='product':value['offers']=offers(raw)
  else:
   text=plain(raw)
   if len(text)<200:raise ValueError('Empty or JS-only content')
   value['fingerprint']=hashlib.sha256(text.encode()).hexdigest()
  return value
 except Exception as e:return {'id':key,'name':name,'url':url,'topic':topic,'ok':False,'checkedAt':NOW,'error':str(e)[:140]}
def merge_records(old,new,limit):
 merged={}
 for item in old+new:merged[(item.get('url'),item.get('title'))]=item
 return list(merged.values())[-limit:]
def main():
 previous=json.loads((ROOT/'content/monitor.json').read_text()) if (ROOT/'content/monitor.json').exists() else {'sources':[],'history':[]}
 previous_sources={s['id']:s for s in previous['sources']}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(collect,SOURCES))
 changes=[];headlines=[]
 for s in results:
  old=previous_sources.get(s['id'],{});last=old if old.get('ok') else old.get('lastGood',{})
  if s['ok']:
   s['lastSuccess']=NOW
   if s.get('items'):
    oldlinks={i['url'] for i in last.get('items',[])}
    new=[i for i in s['items'] if i['url'] not in oldlinks]
    # On first run, present headlines as existing references, never today's breaking news.
    for i in new[:5]:headlines.append({**i,'source':s['name'],'topic':s['topic'],'initial':not bool(last)})
   if s.get('stations') and last.get('stations'):
    oldurls={i['url'] for i in last['stations']};new=[i for i in s['stations'] if i['url'] not in oldurls]
    for i in new:changes.append({'title':'公式一覧に新規掲載：'+i['name'],'url':i['url'],'note':'検出日と開業日は異なります。営業開始・出力は公式詳細と車内地図で確認。'})
   if 'recalls' in s:
    old_ids={i['id'] for i in last.get('recalls',[])}
    for r in s['recalls']:
     if r['id'] not in old_ids:
      changes.append({'title':('米国リコール参考：' if not last else '米国リコールAPIで新規検出：')+str(r['id']),'url':s['url'],'note':'Tesla Model Y 2026の限定検索。対象部品：'+str(r['component'])+'。日本への適用、FSDとの関連は未判定。'})
   if s.get('offers') and s.get('offers')!=last.get('offers'):
    changes.append({'title':s['name']+'：構造化された販売情報を検出','url':s['url'],'note':json.dumps(s['offers'],ensure_ascii=False)+'。配送先や購入時点の在庫は商品画面で再確認。'})
   if s.get('fingerprint') and last.get('fingerprint') and s['fingerprint']!=last['fingerprint']:
    changes.append({'title':s['name']+'：ページ本文の変更候補','url':s['url'],'note':'サイト共通部分の変更も含むため、解禁・値上げ・機能追加は未判定。原文確認が必要です。'})
  else:
   if last:s['lastGood']={k:v for k,v in last.items() if k!='lastGood'};s['lastSuccess']=last.get('lastSuccess',last.get('checkedAt'))
 history=previous.get('history',[]);day=NOW[:10]
 history=[x for x in history if x['date']!=day]+[{'date':day,'ok':sum(s['ok'] for s in results),'total':len(results),'stations':next((len(s['stations']) for s in results if s.get('stations')),None)}]
 report={'checkedAt':NOW,'sources':results,'history':history[-90:]}
 (ROOT/'content/monitor.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'content/reports').mkdir(exist_ok=True)
 (ROOT/'content/reports'/f'{day}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 for p in sorted((ROOT/'content/reports').glob('*.json'))[:-365]:p.unlink()
 existing_path=ROOT/'content/daily'/f'{day}.json'
 if existing_path.exists():
  existing=json.loads(existing_path.read_text())
  headlines=merge_records(existing.get('headlines',[]),headlines,30)
  changes=merge_records(existing.get('changes',[]),changes,50)
 article={'id':'daily-'+day,'date':day,'checkedAt':NOW,'category':'日次レポート','hardware':['HW3','HW4'],'title':day.replace('-','.')+'｜FSD・充電の定点観測','summary':f"公式発表・世界FSD報道・充電情報の{len(results)}系統中、{sum(s['ok'] for s in results)}系統を取得。取得できなかった情報も明示します。",'auto':True,'changes':changes,'headlines':headlines[:30],'photos':['model3','supercharger','modely'],'sources':[{'name':s['name'],'url':s['url']} for s in results]}
 (ROOT/'content/daily').mkdir(exist_ok=True)
 (ROOT/'content/daily'/f'{day}.json').write_text(json.dumps(article,ensure_ascii=False,indent=2)+'\n')
 # Keep 365 days of daily articles; image assets are shared, never duplicated per post.
 for p in sorted((ROOT/'content/daily').glob('*.json'))[:-365]:p.unlink()
 print(json.dumps({'successful':sum(s['ok'] for s in results),'total':len(results),'changes':len(changes),'headlines':len(headlines)}))
 if not any(s['ok'] for s in results):raise SystemExit('All sources failed; do not publish a fresh-looking site')
NOW=dt.datetime.now(TZ).isoformat(timespec='seconds')
if __name__=='__main__':main()
