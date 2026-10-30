"""Summarise public listing-price bins. Never infer transaction prices or HW."""
import re,html
from html.parser import HTMLParser
class FirstTable(HTMLParser):
 def __init__(self):super().__init__();self.depth=0;self.done=False;self.rows=[];self.row=[];self.cell=None;self.links=[]
 def handle_starttag(self,t,a):
  if self.done:return
  if t=='table':self.depth+=1
  if self.depth!=1:return
  if t=='tr':self.row=[]
  if t in ('th','td'):self.cell={'text':'','links':[]}
  if t=='a' and self.cell is not None:self.cell['links'].append(dict(a).get('href',''))
 def handle_data(self,s):
  if self.depth==1 and self.cell is not None:self.cell['text']+=s
 def handle_endtag(self,t):
  if self.done:return
  if t=='table' and self.depth:
   self.depth-=1
   if self.depth==0:self.done=True
  if self.depth!=1:return
  if t in ('th','td') and self.cell is not None:self.row.append(self.cell);self.cell=None
  if t=='tr' and self.row:self.rows.append(self.row)
def integer(cell):
 m=re.search(r'\d+',cell['text'].replace(',',''));return int(m[0]) if m else 0
def summarise(raw):
 p=FirstTable();p.feed(raw);rows=p.rows
 if len(rows)<4 or '相場' not in rows[0][0]['text']:raise ValueError('Market table missing')
 years=[re.sub(r'\s+','',x['text']) for x in rows[0][1:]]
 totals=[integer(x) for x in rows[1][1:]];total=integer(rows[1][0])
 if len(years)!=len(totals) or sum(totals)!=total:raise ValueError('Market year totals mismatch')
 bins=[]
 for row in rows[2:]:
  if len(row)!=len(years)+2:raise ValueError('Market columns changed')
  links=' '.join(row[1]['links']);m=re.search(r'PMIN=(\d*)&(?:amp;)?PMAX=(\d*)',links)
  counts=[integer(c) for c in row[2:]]
  if not any(counts):continue
  if not m:raise ValueError('Market price bounds missing')
  lo=int(m[1])/10000 if m[1] else 0;hi=(int(m[2])+1)/10000 if m[2] else None
  bins.append({'lo':lo,'hi':hi,'counts':counts})
 out=[]
 for col,(year,n) in enumerate(zip(years,totals)):
  if sum(b['counts'][col] for b in bins)!=n:raise ValueError('Market bins do not reconcile')
  if not n:continue
  ranked=[];running=0
  for b in sorted(bins,key=lambda b:b['lo']):
   start=running+1;running+=b['counts'][col]
   if any(start<=rank<=running for rank in ((n+1)//2,(n+2)//2)):ranked.append(b)
  if not ranked:raise ValueError('Median bin missing')
  lo=min(b['lo'] for b in ranked);hi=None if any(b['hi'] is None for b in ranked) else max(b['hi'] for b in ranked)
  out.append({'year':year,'count':n,'medianLowerManYen':lo,'medianUpperManYen':hi,'smallSample':n<10})
 return {'listingCount':total,'years':out,'measure':'車両本体の掲載価格分布から求めた中央値の所属範囲（万円）。成約価格ではありません。'}
