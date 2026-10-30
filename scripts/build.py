import datetime as dt,hashlib,html,json,os,shutil,xml.etree.ElementTree as ET
from pathlib import Path
from hardware_page import render as hardware_html
from market_page import snapshot as market_snapshot, render as market_html
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist'
CSSVER=hashlib.sha256((ROOT/'assets/style.css').read_bytes()).hexdigest()[:12]
JSVER=hashlib.sha256((ROOT/'assets/app.js').read_bytes()).hexdigest()[:12]
BASE=os.environ.get('SITE_URL','https://clipcore-dev.github.io/tesla-japan-watch').rstrip('/')
e=lambda x:html.escape(str(x),quote=True)
def read(p):return json.loads((ROOT/p).read_text())
images={i['id']:i for i in read('content/images.json')}
monitor=read('content/monitor.json')
articles=read('content/articles.json');daily=[json.loads(p.read_text()) for p in sorted((ROOT/'content/daily').glob('*.json'),reverse=True)]
allposts=daily+articles
reports=[json.loads(p.read_text()) for p in sorted((ROOT/'content/reports').glob('*.json'))]
if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir();shutil.copytree(ROOT/'assets',OUT/'assets')

def photo(key,prefix='',hero=False):
 i=images[key]
 return f'''<figure class="{'hero-photo' if hero else 'article-photo'}"><img src="{prefix}{e(i['path'])}" alt="{e(i['caption'])}" {'fetchpriority="high"' if hero else 'loading="lazy"'} width="1600" height="900"><figcaption>{e(i['caption'])}<br><a href="{e(i['source'])}">{e(i['author'])} / Wikimedia Commons</a> · <a href="{e(i['licenseUrl'])}">{e(i['license'])}</a> · {e(i['changes'])}</figcaption></figure>'''
def table(t):return '<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+e(x)+'</th>' for x in t['headers'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+e(x)+'</td>' for x in row)+'</tr>' for row in t['rows'])+'</tbody></table></div>'
def shell(title,body,prefix='',path='',description='日本のHW3・HW4オーナーのための独立系Teslaニュース。FSD・充電・Superchargerを出典と確認日つきで。'):
 structured=json.dumps({'@context':'https://schema.org','@type':'WebSite' if not path else 'WebPage','name':title,'url':BASE+'/'+path,'inLanguage':'ja'},ensure_ascii=False).replace('<','\\u003c')
 return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#c63b32"><title>{e(title)} | TESLA JAPAN WATCH</title><meta name="description" content="{e(description)}"><link rel="canonical" href="{BASE}/{e(path)}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><meta property="og:type" content="website"><meta property="og:image" content="{BASE}/assets/photos/model3.jpg"><link rel="icon" href="{prefix}assets/icon.svg"><link rel="apple-touch-icon" href="{prefix}assets/icon-192.png"><link rel="stylesheet" href="{prefix}assets/style.css?v={CSSVER}"><link rel="manifest" href="{prefix}manifest.webmanifest"><link rel="alternate" type="application/rss+xml" title="Tesla Japan Watch" href="{prefix}feed.xml"><script type="application/ld+json">{structured}</script><script defer data-app src="{prefix}assets/app.js?v={JSVER}"></script></head><body><a class="skip" href="#main">本文へ</a><div class="topline"><span>INDEPENDENT TESLA JOURNAL</span><span>HW3 / HW4 · JAPAN</span></div><header><a class="brand" href="{prefix}index.html">TESLA<span>JAPAN WATCH<span class="brand-dot">●</span></span></a><nav aria-label="メイン"><a href="{prefix}index.html#latest">ニュース</a><a href="{prefix}index.html#guides">オーナーズガイド</a><a href="{prefix}index.html#monitor">定点観測</a><a href="{prefix}archive.html">記事一覧</a><a href="{prefix}about.html">運営方針</a><a class="rss" href="{prefix}feed.xml">RSS ↗</a></nav></header><main id="main">{body}</main><footer><strong>TESLA JAPAN WATCH</strong><p>日本のオーナーへ、事実と、その先を。Teslaとは関係のない独立サイトです。</p><p><a href="{prefix}about.html">運営・費用・画像ライセンス</a> <a href="https://github.com/clipcore-dev/tesla-japan-watch">GitHub ↗</a> <a href="{prefix}feed.xml">RSS</a></p><small>事実・報道・予測を区別。情報は各確認日時点のものです。FSDはドライバーの監視を必要とします。</small></footer></body></html>'''
def card(a):
 image=images[a['photos'][0]];return f'''<article class="card" data-search="{e(a['title']+' '+a['summary']+' '+a['category'])}" data-category="{e(a['category'])}" data-id="{e(a['id'])}"><a href="articles/{a['id']}.html" tabindex="-1" aria-hidden="true"><img src="{image['path']}" alt="" loading="lazy" width="640" height="360"></a><p class="card-credit"><a href="{e(image['source'])}">写真：{e(image['author'])}</a> / <a href="{e(image['licenseUrl'])}">{e(image['license'])}</a>（縮小・表示枠でトリミング）</p><div class="card-body"><div class="eyebrow">{e(a['category'])}<span>{e(a['date'])}</span></div><h3><a href="articles/{a['id']}.html">{e(a['title'])}</a></h3><p>{e(a['summary'])}</p><div class="tags"><span>HW3</span><span>HW4</span><span>{'自動定点観測' if a.get('auto') else '出典付きガイド'}</span></div></div></article>'''
def error_label(s):
 raw=s.get('error','')
 if '403' in raw:return 'アクセス制限により自動取得できません'
 if '404' in raw:return 'ページを確認できません（販売終了や在庫なしとは判定しません）'
 return '取得失敗。取得ログに詳細を記録しています'
def status_table():
 rows=[]
 for s in monitor['sources']:
  st='取得成功' if s['ok'] else '取得不可・未確認'
  detail=''
  if s.get('stations'):detail=f"一覧 {len(s['stations'])}拠点（営業状態は別途確認）"
  elif 'market' in s:detail=f"本体掲載価格・年式別分布 {s['market']['listingCount']}台"
  elif 'offers' in s:detail='販売構造化データ：'+(json.dumps(s['offers'],ensure_ascii=False) if s['offers'] else 'なし。在庫・価格は未確認')
  elif 'items' in s:detail=f"見出し {len(s['items'])}件（発表日を原文で確認）"
  elif 'recalls' in s:detail=f"リコール {len(s['recalls'])}件／当該モデル・年式のみ"
  elif not s['ok']:detail=error_label(s)
  rows.append([s['name'],st,detail,s.get('lastSuccess','なし')])
 rendered=table({'headers':['情報源','取得状態','範囲・注意','最後の取得成功（JST）'],'rows':rows})
 for source in monitor['sources']:rendered=rendered.replace('<td>'+e(source['name'])+'</td>','<td><a href="'+e(source['url'])+'">'+e(source['name'])+' ↗</a></td>')
 return rendered
now=monitor['checkedAt'];ok=sum(s['ok'] for s in monitor['sources'])
hero=f'''<section class="hero"><div class="hero-copy"><div class="eyebrow">FOR JAPAN'S TESLA OWNERS</div><h1>進化を追う。<br>自分のTeslaで<br><em>考える。</em></h1><p>購入・補助金・中古相場から、FSDと充電まで。<br>これから買う人にも、いま乗っている人にも。</p><a class="button" href="articles/japan-fsd.html">今日の確認ポイント <span>↗</span></a><div class="hero-meta">独立系ニュース / 出典付き / 日本語</div></div>{photo('model3',hero=True)}</section>'''
body=hero+f'''<div class="status-strip"><span class="pulse"></span><strong>MONITOR</strong><span>最終実行 {e(now)}</span><span class="status-count">{ok}/{len(monitor['sources'])} 系統取得</span><a href="#monitor">取得状態を見る ↗</a></div><section class="intro-grid"><div><span class="kicker">01 / FSD</span><h2>日本への提供時期は、<br>公式の案内を待つ。</h2><p>解禁・地域・契約・配信を分けて確認。海外のアップデートを日本の実車に当てはめません。</p></div><div><span class="kicker">02 / HARDWARE</span><h2>年式より、<br>実車の確認を。</h2><p>日本向けの車種・切替期を整理。VINと製造時期、在庫車・交換済み車の例外も。</p></div><div><span class="kicker">03 / CHARGING</span><h2>買えることと、<br>使えること。</h2><p>200V設備、アダプターの在庫、Superchargerの新規掲載。それぞれの根拠を添えて。</p></div></section><section id="latest"><div class="section-head"><div><span class="kicker">THE JOURNAL</span><h2>最新記事とオーナーズガイド</h2></div><span>{len(allposts)} ARTICLES</span></div><div class="filters"><div class="filter-buttons" role="group" aria-label="記事カテゴリ">'''+''.join(f'<button data-filter="{e(v)}" aria-pressed="{str(i==0).lower()}">{e(v)}</button>' for i,v in enumerate(['すべて','日次レポート','購入・キャンペーン','補助金','中古相場','FSD・世界','HW3・HW4','充電・在庫','Supercharger','アップデート','アクセサリー']))+'''</div><label class="search-label">記事を検索<input id="search" type="search" placeholder="FSD、200V、HW3…"></label></div><div class="cards" id="cards">'''+''.join(card(a) for a in allposts[:24])+'''</div><div id="global-results" aria-live="polite"></div><p class="archive-link"><a href="archive.html">過去の記事をすべて読む ↗</a> · <a href="market.html">モデル別・年式別の中古相場 ↗</a></p><p id="empty" hidden>該当する記事がありません。</p></section><section id="guides" class="guide-band"><div><span class="kicker">KNOW YOUR TESLA</span><h2>あなたの一台から、<br>ニュースを読む。</h2><p>年式とハードウェアの確認から始めましょう。<br>VINの入力・送信は不要です。</p></div><div class="guide-links"><a href="articles/subsidy-2026.html">購入キャンペーン・補助金の確認 <span>↗</span></a><a href="market.html">モデル別・年式別の中古相場 <span>↗</span></a><a href="articles/hardware-guide.html">車種・年式別 HW3 / HW4 確認表 <span>↗</span></a><a href="articles/charging-guide.html">200V・充電アクセサリーガイド <span>↗</span></a><a href="articles/supercharger-watch.html">Supercharger 新規掲載の読み方 <span>↗</span></a></div></section><section id="monitor"><div class="section-head"><div><span class="kicker">SOURCE TRANSPARENCY</span><h2>取れた情報も、取れなかった情報も。</h2></div></div><p class="muted">毎日07:23 JSTに実行予定（GitHubの混雑で遅延する場合があります）。取得失敗は「変更なし」「在庫なし」を意味しません。RSSの見出しは報道発見用で、事実確認済みの日本向けニュースとは区別します。</p>'''+status_table()+'''<p><a href="data/monitor.json">取得ログ（JSON） ↗</a> · <a href="https://github.com/clipcore-dev/tesla-japan-watch/actions">自動更新の実行履歴 ↗</a></p></section>'''
(OUT/'index.html').write_text(shell('日本のHW3・HW4オーナーへ',body))
(OUT/'articles').mkdir()
# A permanent, paginated archive avoids inflating the home page.
archive_pages=max(1,(len(allposts)+23)//24)
for page in range(archive_pages):
 name='archive.html' if page==0 else f'archive-{page+1}.html'
 entries=allposts[page*24:(page+1)*24]
 archive='<section><div class="section-head"><div><span class="kicker">THE COMPLETE ARCHIVE</span><h1>過去の記事も、残していく。</h1></div></div><p>公開した記事は日付と確認時点を残して蓄積します。古いキャンペーンや補助金を、現在も有効とは扱いません。</p><div class="cards">'+''.join(card(a) for a in entries)+'</div><nav class="pagination" aria-label="アーカイブのページ">'+''.join('<a href="'+('archive.html' if i==0 else f'archive-{i+1}.html')+'">'+str(i+1)+'</a>' for i in range(archive_pages))+'</nav></section>'
 (OUT/name).write_text(shell('記事アーカイブ '+str(page+1),archive,path=name))
(OUT/'market.html').write_text(shell('中古Tesla相場の定点観測',market_html(reports),path='market.html'))
for a in allposts:
 body=f'''<div class="article-top"><a href="../index.html#latest">← 記事一覧</a><span>{e(a['category'])} / {e(a['date'])}</span></div><article class="reading"><div class="eyebrow">HW3 + HW4 · {'AUTOMATED SOURCE MONITOR' if a.get('auto') else 'OWNER’S GUIDE'}</div><h1>{e(a['title'])}</h1><p class="standfirst">{e(a['summary'])}</p><p class="article-meta">{'自動取得・定型文生成。AI APIは使用していません。' if a.get('auto') else '編集確認：'+a['date']+'。この記事の本文は日次監視で自動改稿しません。'} <button class="share">リンクをコピー</button></p>'''+('' if a['id']=='hardware-guide' else photo(a['photos'][0],'../'))
 if a['id']=='hardware-guide':body+=hardware_html(read('content/hardware.json'))
 if a.get('marketLink'):body+='<p><a class="button" href="../market.html">本日のモデル別・年式別相場を見る ↗</a></p>'
 if a.get('auto'):
  body+='<div class="notice">これは取得結果の日本語レポートです。海外見出しは未検証の報道案内。国内の解禁・在庫・開業を自動認定する記事ではありません。</div><h2>今回検出した更新</h2>'
  if a['changes']:
   for c in a['changes']:body+=f'<h3><a href="{e(c["url"])}">{e(c["title"])}</a></h3><p>{e(c["note"])}</p>'
  else:body+='<p>確定できる新規掲載・構造化販売情報の変化はありませんでした。取得できなかった情報源について変化がないとは判断できません。</p>'
  body+='<h2>公式発表・海外報道への入口</h2><p>初回取得時の見出しは既存の参考記事です。見出しの掲載順と公開日は原文で確認してください。過去記事の再配信もあり得ます。</p><ul class="headlines">'
  for h in a['headlines']:body+=f'<li><span class="kicker">{e(h["topic"])} · {"初回参考" if h["initial"] else "新規検出"}</span><a href="{e(h["url"])}">{e(h["title"])}</a><small>{e(h["source"])} / 原文公開日 {e(h["published"] or "不明")}</small></li>'
  body+='</ul><h2>日本のオーナーへの確認ポイント</h2><p>HW3・HW4とも、海外の提供開始・価格・バージョンを国内条件へ直接適用しないでください。在庫は公式商品画面、新しい充電拠点は公式詳細と車内地図を確認します。国内の開始時期を推定できる新たな根拠は、この定型レポートでは認定していません。</p>'
  # Freeze each daily report to its corresponding acquisition results, not latest monitor.
  report=read('content/reports/'+a['date']+'.json') if (ROOT/'content/reports'/f"{a['date']}.json").exists() else monitor
  body+='<h2>購入前・オーナー向け：今日の確認ポイント</h2><p>購入特典は対象車・期限・残枠、補助金は登録日別の額・申請期限・予算終了見込みを分けて確認。FSDはHWと契約、アップデートは日本向け配信条件を確認します。アクセサリーは車両世代・実寸・国内販売条件を照合します。</p><h2>本日のモデル別・年式別中古相場</h2>'+market_snapshot(report)+'<h2>この日の取得状況</h2><figure><img class="chart" src="../assets/coverage-'+a['date']+'.svg" alt="情報源の取得成功数と未確認数。FSDの普及率や安全性能を示すグラフではありません。"><figcaption>編集部作成：この日の自動取得結果。情報源の取得率であり、ニュースの真偽やFSDの安全性を示す指標ではありません。</figcaption></figure>'+table({'headers':['情報源','状態','確認時刻'],'rows':[[s['name'],'取得成功' if s['ok'] else '未確認 / '+error_label(s),s['checkedAt']] for s in report['sources']]})
 else:
  for i,s in enumerate(a['sections']):
   body+=f'<h2>{e(s["heading"])}</h2><p>{e(s["text"])}</p>'
   if i==1 and a.get('table'):body+=table(a['table'])
   if i==1 and a.get('chartAsset'):body+='<figure><img class="chart" src="../assets/'+e(a['chartAsset'])+'" alt="'+e(a['title'])+'の比較図"><figcaption>編集部作成。数値・条件・出典は本文と表を参照。</figcaption></figure>'
   if i==1 and a.get('chart'):body+='<figure><img class="chart" src="../assets/charging.svg" alt="理論入力は100V 12Aで1.2kW、200V 16Aで3.2kW。実測ではありません。"><figcaption>編集部作成：電圧×電流÷1000。Tesla公式モバイルコネクターの電流仕様を使用。実測値ではありません。</figcaption></figure>'
 if a.get('auto'):
  n=sum(x['ok'] for x in report['sources']);total=len(report['sources']);w=int(650*n/max(total,1))
  (OUT/'assets'/('coverage-'+a['date']+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="820" height="180" viewBox="0 0 820 180"><rect width="820" height="180" fill="#eeeee7"/><text x="40" y="42" font-family="sans-serif" font-size="20">情報源の取得状況 / {a["date"]}</text><rect x="40" y="70" width="650" height="35" fill="#d7d8d0"/><rect x="40" y="70" width="{w}" height="35" fill="#456a57"/><text x="40" y="143" font-family="sans-serif" font-size="16">取得成功 {n}系統 / 未確認 {total-n}系統（全{total}系統）</text></svg>')
 if a['id']=='hardware-guide':body+=photo(a['photos'][0],'../')
 body+=photo(a['photos'][1],'../')
 if len(a['photos'])>2:body+=photo(a['photos'][2],'../')
 body+='<aside class="sources"><h2>出典・確認先</h2><ol>'+''.join(f'<li><a href="{e(s["url"])}">{e(s["name"])}</a></li>' for s in a['sources'])+'</ol><p>写真は参考写真です。撮影された車両のハードウェア、最新機能、日本仕様を保証しません。画像ごとの作者・ライセンス・変更内容をキャプションに記載しています。</p></aside><a class="button" href="../index.html#latest">ほかの記事を読む ↗</a></article>'
 (OUT/'articles'/f"{a['id']}.html").write_text(shell(a['title'],body,'../','articles/'+a['id']+'.html',a['summary']))
about='''<article class="reading"><span class="kicker">ABOUT THIS JOURNAL</span><h1>透明に調べ、<br>無理なく続ける。</h1><p class="standfirst">Tesla Japan Watchは、日本のHW3・HW4オーナー向けの独立ニュースブログ兼Webアプリです。Teslaの公式媒体ではありません。</p><h2>運営と編集の方針</h2><p>運営：clipcore-dev。事実は出典・確認日・地域を付記。海外の報道、メーカーの計画、編集部の予測を区別します。規制の最終判断、電気工事、個別車両の仕様は専門の窓口・公式情報で確認してください。訂正はGitHub Issuesへお寄せください。</p><h2>無料で動く範囲</h2><p>公開GitHubリポジトリ、標準のubuntu-latestランナー、GitHub Pagesを利用。日次レポートは無料のHTTP・RSS・JSON APIと定型文で生成します。有料AI API、画像生成API、課金サービスの呼び出し、広告、アクセス解析は実装していません。ブラウザーのホーム画面へ追加できるPWAです。</p><h2>無料枠と停止条件</h2><p>公開リポジトリの標準GitHubホストランナーは無料です。Pagesの公開サイトは最大1GB、帯域のソフト上限は月100GB。大きいランナーは有料のため使いません。成果物保存は1日、記事と日別集計は削除せず蓄積し、画像は圧縮した3枚を全記事で共有します。ホームは24件、過去分はページ分割した一覧に掲載します。無制限運用を保証するものではなく、GitHubや取得元の制限・仕様変更で停止や遅延が起こり得ます。</p><p>毎日07:23 JST予定。取得結果は日次でリポジトリに保存します。GitHubでは公開リポジトリの活動が60日間ないと定期実行が無効になることがあります。日次保存の成功中はコミットが発生しますが、失敗が続いた場合はActionsで手動再開が必要です。</p><h2>AI料金と記事の範囲</h2><p>現状のAI API利用料は0円です。自由文の長文ニュース解説や新しい実写写真の自動生成はしていません。自動で公開するのは出典付きの差分・取得状況レポートで、ガイド本文は編集時点の情報です。将来有料AIを追加する際は、利用者が別途料金を確認し、明示的に承認・設定する必要があります。既存ChatGPTタスクやこのチャットを読み出す仕組みはありません。</p><h2>画像と権利</h2><p>Wikimedia Commonsの個別画像で確認したCC BY-SA 4.0またはCC0の実写写真のみをローカル配信します。作者、元画像、ライセンスへのリンク、縮小・トリミングの表示を付けています。CC BY-SA画像の改変物にも同じライセンスを適用します。サイト全体やTeslaの商標が同ライセンスという意味ではありません。Tesla公式サイトの写真や報道写真を無断転載しません。</p><h2>自動取得の限界</h2><p>Teslaが403などを返すときは回避せず、未確認を表示。ページ本文の変更は解禁・値上げ・入荷を意味しません。在庫はJSON-LD Offerの明示値のみ、Superchargerは正常に取得できた公式一覧同士のリンク差分のみを記録。新規掲載を開業とは呼びません。NHTSA APIは米国Model Y 2026のリコールを対象とする限定的な補助情報です。オランダRDWの承認説明ページと規制当局の関連発表を探すRSSも監視しますが、全世界の規制監視を網羅していません。海外RSSは報道発見用で真偽を自動認定しません。</p><h2>個人情報と保存</h2><p>ログイン、VIN入力、メール収集はありません。外部リンク先の規約は各提供元のものです。PWAは閲覧済みのページを端末に保存します。削除はブラウザーのサイトデータ管理から行えます。ホスティング側のアクセスログはGitHubのプライバシー規約が適用されます。</p><h2>条件の出典</h2><ul><li><a href="https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits">GitHub Pagesの制限</a></li><li><a href="https://docs.github.com/en/billing/concepts/product-billing/github-actions">Actionsの料金</a></li><li><a href="https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule">定期実行の制限</a></li><li><a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a></li></ul><p><a href="https://github.com/clipcore-dev/tesla-japan-watch/issues">訂正・お問い合わせ（GitHub Issues） ↗</a></p></article>'''
(OUT/'about.html').write_text(shell('運営・費用・画像の利用条件',about,path='about.html'))
(OUT/'offline.html').write_text(shell('オフライン','<article class="reading"><h1>接続を確認してください。</h1><p>このページはまだ端末に保存されていません。</p><a href="index.html">ホームへ</a></article>',path='offline.html'))
(OUT/'data').mkdir();
(OUT/'data/search.json').write_text(json.dumps([{k:a[k] for k in ('id','title','summary','category','date')} for a in allposts],ensure_ascii=False,separators=(',',':')))
(OUT/'data/monitor.json').write_text(json.dumps(monitor,ensure_ascii=False,separators=(',',':')));shutil.copy(ROOT/'content/images.json',OUT/'data/images.json')
(OUT/'manifest.webmanifest').write_text(json.dumps({'name':'Tesla Japan Watch','short_name':'Tesla Watch','lang':'ja','id':'./','start_url':'./','scope':'./','display':'standalone','background_color':'#f7f6f2','theme_color':'#c63b32','icons':[{'src':'assets/icon-192.png','sizes':'192x192','type':'image/png'},{'src':'assets/icon-512.png','sizes':'512x512','type':'image/png'}]},ensure_ascii=False))
import hashlib
version=hashlib.sha256(''.join(p.read_text() for p in OUT.glob('*.html')).encode()).hexdigest()[:12]
(OUT/'sw.js').write_text('''const CACHE="tjw-'''+version+'''";self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(c=>c.addAll(['./','index.html','offline.html','assets/style.css','assets/app.js','assets/icon.svg'])));self.skipWaiting()});self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('tjw-')&&k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim()});self.addEventListener('fetch',event=>{if(event.request.method!=='GET'||new URL(event.request.url).origin!==location.origin)return;event.respondWith(fetch(event.request).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE).then(c=>c.put(event.request,copy))}return response}).catch(()=>caches.match(event.request).then(r=>r||(event.request.mode==='navigate'?caches.match(new URL('offline.html',self.registration.scope).href):Response.error()))))});''')
sw=OUT/'sw.js'
sw.write_text(sw.read_text().replace("'assets/style.css'","'assets/style.css?v="+CSSVER+"'").replace("'assets/app.js'","'assets/app.js?v="+JSVER+"'"))
# RSS uses escaped XML and absolute project URLs.
rss=ET.Element('rss',version='2.0');ch=ET.SubElement(rss,'channel')
for tag,text in [('title','Tesla Japan Watch'),('link',BASE+'/'),('description','日本のHW3・HW4オーナー向けのニュースと定点観測'),('language','ja')]:ET.SubElement(ch,tag).text=text
for a in allposts[:40]:
 item=ET.SubElement(ch,'item')
 for tag,text in [('title',a['title']),('link',BASE+'/articles/'+a['id']+'.html'),('guid',BASE+'/articles/'+a['id']+'.html'),('description',a['summary']),('pubDate',dt.datetime.fromisoformat(a['date']).strftime('%a, %d %b %Y 00:00:00 GMT'))]:ET.SubElement(item,tag).text=text
ET.ElementTree(rss).write(OUT/'feed.xml',encoding='utf-8',xml_declaration=True)
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(BASE+'/'+p)+'</loc></url>' for p in ['','about.html','market.html','archive.html']+['articles/'+a['id']+'.html' for a in allposts])+'</urlset>')
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+BASE+'/sitemap.xml\n');(OUT/'.nojekyll').touch()
print(f'Built {len(allposts)} articles; {sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())/1e6:.2f} MB')
