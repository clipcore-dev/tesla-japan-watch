import html
E=lambda x:html.escape(str(x),quote=True)
def table_for(source):
 m=source['market'];out='<h3>'+E(source['name'])+'</h3><p class="muted">取得 '+E(source['checkedAt'])+' / 掲載 '+str(m['listingCount'])+'台。出典：<a href="'+E(source['url'])+'">掲載価格分布 ↗</a></p><div class="table-wrap"><table><thead><tr><th>登録年の区分</th><th>掲載台数</th><th>中央値が属する範囲（本体価格）</th><th>注意</th></tr></thead><tbody>'
 for r in m['years']:
  lo=r['medianLowerManYen'];hi=r['medianUpperManYen'];band=f'{lo:g}万円以上' if hi is None else f'{lo:g}万円以上〜{hi:g}万円未満'
  out+='<tr>'+''.join('<td>'+E(x)+'</td>' for x in [r['year'],str(r['count'])+'台',band,'少数標本（10台未満）' if r['smallSample'] else '掲載価格・成約価格ではない'])+'</tr>'
 out+='</tbody></table></div>'
 if m.get('excludedListings'):out+='<p class="muted">国内導入前の年式区分 '+str(m['excludedListings'])+'台を表から除外。入力誤りや並行輸入を自動判定していません。</p>'
 return out

def snapshot(report):
 found=[s for s in report['sources'] if s.get('ok') and s.get('market')]
 if not found:return '<p>この日の中古相場データは取得できませんでした。前回値を今日の相場として表示しません。</p>'
 return '<p>元データ：カーセンサーの公開相場表。価格帯ごとの分布から中央値の所属範囲を求めたものです。グレード・距離・修復歴の構成をそろえた指数ではありません。</p>'+''.join(table_for(s) for s in found)
def render(reports):
 out='<article class="reading wide-reading"><span class="kicker">USED TESLA / MARKET OBSERVATIONS</span><h1>モデル別・年式別、<br>中古相場の記録。</h1><p class="standfirst">Model 3・Y・S・Xの本体掲載価格を日々観測。正確な成約価格や、FSDによる価格差を示すものではありません。</p>'
 good=[r for r in reports if any(s.get('market') and s.get('ok') for s in r['sources'])]
 out+='<div class="notice">'+('観測はまだ1日分です。前日比・月次推移はデータが蓄積してから比較します。' if len(good)<2 else str(len(good))+'日分を記録しています。以下の履歴で各日の相場表を比較できます。')+' 少数区分や掲載構成の変化には注意してください。</div>'
 if reports:out+='<h2>直近の取得結果</h2>'+snapshot(reports[-1])
 if len(good)>1:
  previous,current=good[-2:];before={s['id']:s for s in previous['sources'] if s.get('ok') and s.get('market')}
  out+='<h2>前回観測との比較</h2><p>比較日は '+E(previous['checkedAt'][:10])+' と '+E(current['checkedAt'][:10])+'。日付が離れた場合は前日比ではありません。価格範囲は元の掲載分布の区切りにも影響されます。車両構成の変化やFSDの因果効果を調整した指数ではありません。</p><div class="table-wrap"><table><thead><tr><th>車種・年式</th><th>前回の中央値所属範囲</th><th>今回の中央値所属範囲</th><th>掲載台数の差</th></tr></thead><tbody>'
  def band(r):
   lo,hi=r['medianLowerManYen'],r['medianUpperManYen']
   return f'{lo:g}万円以上' if hi is None else f'{lo:g}〜{hi:g}万円未満'
  for source in current['sources']:
   if not source.get('ok') or not source.get('market') or source['id'] not in before:continue
   old={r['year']:r for r in before[source['id']]['market']['years']}
   for r in source['market']['years']:
    if r['year'] not in old:continue
    prev=old[r['year']];name=source['name'].replace('カーセンサー ','').replace(' 掲載価格相場','')+' / '+r['year']
    out+='<tr>'+''.join('<td>'+E(x)+'</td>' for x in [name,band(prev),band(r),f"{r['count']-prev['count']:+d}台"])+'</tr>'
  out+='</tbody></table></div>'
 out+='<h2>日付別の記録</h2><ul>'
 for r in reversed(good):
  date=r['checkedAt'][:10];out+='<li><a href="articles/daily-'+date+'.html">'+E(date)+'の中古相場・日次トピックス</a></li>'
 return out+'</ul><p><a href="articles/used-market-and-fsd.html">FSDの将来と中古価値をどう分けて考えるか ↗</a></p></article>'
