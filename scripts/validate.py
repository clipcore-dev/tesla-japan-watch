"""Check every local HTML/CSS/JS/image link before deploying."""
from html.parser import HTMLParser
from pathlib import Path
import json,urllib.parse,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist'
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,a):
  for k,v in a:
   if k in ('src','href') and v:self.links.append(v)
def main():
 errors=[]
 for page in OUT.rglob('*.html'):
  p=Links();p.feed(page.read_text())
  for link in p.links:
   url=urllib.parse.urlparse(link)
   if url.scheme or url.netloc or not url.path:continue
   dest=(page.parent/urllib.parse.unquote(url.path)).resolve()
   if not dest.is_relative_to(OUT.resolve()) or not dest.exists():errors.append(f'{page.name}: broken local link {link}')
 for i in json.loads((ROOT/'content/images.json').read_text()):
  assert i['author'] and i['licenseUrl'] and i['source'] and i['changes']
  assert i['license'] in ('CC BY-SA 4.0','CC0')
  path=OUT/i['path'];assert path.read_bytes().startswith(b'\xff\xd8')
 for name in ('feed.xml','sitemap.xml'):ET.parse(OUT/name)
 assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())<900_000_000
 if errors:raise SystemExit('\n'.join(errors))
 print('Validated all internal links, XML feeds, image licences and size cap')
if __name__=='__main__':main()
