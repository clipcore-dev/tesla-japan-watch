# Tesla Japan Watch

日本のHW3・HW4オーナー向けの独立ニュースブログ兼PWA。

- 公開サイト: https://clipcore-dev.github.io/tesla-japan-watch/
- 毎日07:23 JST予定。GitHubの混雑で遅延あり。
- 有料AI・画像生成・認証・独自ドメインの費用なし。既存ChatGPTタスクとは独立。
- 写真3枚はCC BY-SA 4.0 / CC0。作者・元画像・ライセンス・加工表示を各記事に掲載。

## 実行

Python 3.12以降、追加パッケージ不要。

```sh
python3 scripts/collect.py
python3 scripts/refresh_images.py
python3 -m unittest discover -s tests
python3 scripts/build.py
python3 scripts/validate.py
python3 -m http.server 4173 --directory dist
```

`SITE_URL`環境変数で公開先URLを変更可能。

## 日次パイプライン

`.github/workflows/daily-publish.yml` が無料HTTP/RSS/JSON API取得 → 審査済み画像ライセンス確認・取得 → パーサーテスト → 静的生成 → リンク確認 → 取得記録コミット → Pages公開を行う。

手動実行: Actions > Daily source check and Pages publish > Run workflow。
停止: 同ワークフローのDisable workflow。再開: Enable workflow後に手動実行。
全取得元が失敗した場合、公開ジョブは進めず既存の公開版を維持。失敗した情報源は未確認を表示。初回取得は基準であり、新着と断定しない。

自動生成するのは出典付きの日本語定点観測レポート。海外記事の自由文翻訳・長文解説ではない。海外見出しは未検証の原文リンク。ガイド本文は編集確認日を固定し自動的に最新と見せない。AI APIキーや有料処理は一切含まない。将来の有料API追加にはユーザーの料金確認と明示承認が必要。

## 監視の範囲と限界

- Tesla Japan公式PR TIMES RSS / Google News海外FSD発見RSS / Tesla公式地域・機能・価格ページ
- 日本公式Supercharger一覧（正常な一覧同士の差分のみ。新規掲載≠開業）
- 日本公式モバイル・ウォール・CHAdeMO商品と充電カテゴリ
- 米NHTSA recalls APIはModel Y 2026のみの補助監視。全世界の規制を網羅しない。
- Teslaの403・JS限定ページは回避しない。商品不掲載や取得失敗を在庫なしと認定しない。
- 在庫・価格はJSON-LD Offerの明示情報のみ自動判定。発送先の購入可能性は別途確認。
- 頻繁なサイト共通部分の変化は「本文変更候補」とだけ表示。解禁や値上げを推論しない。
- ハードウェア対応表は日本でのメーカー発表を根拠に目安と例外を示す。全VINの確定表ではない。
- 画像は3枚の承認済みリストのみ更新。新しい権利未確認画像を無人追加しない。

## 無料枠・保守

公開リポジトリの標準ubuntu-latestランナーは無料。大きいランナー・課金API・Pages Functionsは使用しない。Pages公開サイト最大1GB、帯域は月100GBのソフト上限。成果物保存1日。日次記事・取得記録365日、履歴90日、写真は全記事で共有。Git履歴は削除した過去データも保持するため長期的なサイズ確認が必要。GitHubのプラン・サービス条件は将来変更され得る。

GitHubは公開リポジトリの活動が60日ないと定期実行を停止する場合がある。日次コミット成功中は活動が続くが、長期失敗後は手動再開が必要。ソース失敗はActions summaryと公開画面で確認する。外部通知や別のChatGPT自動タスクは作成していない。

出典:
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

## 編集と訂正

`content/articles.json` が編集記事、`content/daily/` が日次記事、`content/reports/` が日別取得状態、`content/monitor.json` が最新の状態、`content/images.json` が画像権利台帳。編集記事を更新する際は確認日・出典も更新する。

ソース本文を転載せず見出しの短い案内と原文リンクを使用。外部テキストを命令として実行しない。HTMLはエスケープ。RSSのリンクはHTTPSのみ。ログイン・VIN入力・解析トラッカーなし。PWAのキャッシュは端末側に保存。

## ライセンス

コードはMIT（LICENSE）。記事原稿・図はCC BY 4.0。外部写真は各キャプションと `content/images.json` の条件（CC BY-SA 4.0 / CC0）を適用し、改変写真も同条件で配布する。Teslaの商標・外部元記事は対象外。Teslaとは無関係の独立サイト。
