# データ辞書（accounts.csv / videos.csv）
文字コード: UTF-8（BOM付き）。1行1アカウント。取得日 2026-10-03（JST）。生成: `python3 scripts/build.py`（既存調査＋新規Grokランの found.md を毎回取り込み直す）。

## accounts.csv
| 列 | 値・型 | 定義／測り方 | 限界 |
|---|---|---|---|
| platform | TikTok / Instagram / YouTube | 投稿先。InstagramはリールYouTubeはShortsが対象 | |
| genre | 美容スキンケア / ドッグフード / 見守りカメラ / 婚活 | ペット既存行はキーワード規則で再ラベル（見守りカメラ/ペットカメラ/留守番カメラ/Furbo/ebo/Petcube/Tapo等→見守りカメラ、ドッグフード/手作りごはん/食いつき/トッピング/療法食等→ドッグフード、両方なら出現数の多い方）。どちらにも当たらない行は除外 | キーワードのため誤分類あり得る |
| bucket | 伸びてる / 伸び悩み（ユーザー参考アカウントのみ 参考（区分外） / 参考（区分外・投稿停止） もあり） | 伸びてる=直近60日に投稿あり かつ（median_views≥10,000 または median_to_followers≥0.30）。伸び悩み=直近30日4本以上 かつ median_views<500 かつ median_to_followers<0.30 | スクリプトで再判定。満たさない行は落とした |
| bucket_basis | 数値確認 / 代替指標（再生数非公開・調査員判定） | 再生数で判定できたか | Instagramは再生非公開が多い |
| genre_match | 主題 / 一部投稿で言及 / 参考（…）（ユーザー参考アカウント） | ペット再ラベル時、名前に語がある or 3回以上出現=主題。それ以外=一部投稿で言及。新規・美容・婚活は「主題」 | |
| handle | 文字列（小文字、@なし） | アカウントID。YouTubeは@ハンドル（無ければチャンネルID） | |
| account_name | 文字列 | 表示名 | |
| url | URL | プロフィール/チャンネルURL | |
| followers | 整数 | フォロワー数（YouTubeは登録者数）。公開ページの値 | 「1.2万」等の丸め値あり |
| posts_last30_seen | 整数 or 空 | 直近30日の投稿本数（見えた範囲の下限）。YouTubeは「4本目が30日以内」なら4（下限） | 空=不明 |
| recent_views | 「;」区切り整数 | 直近数本の再生数（新しい順。TikTokはembed表示順） | TikTok embedは人気動画と新着が混在 |
| median_views | 数値 | 直近再生の中央値（調査票の記載値、無ければrecent_viewsから計算）。広告で膨らんだ再生は除外済み | |
| median_to_followers | 小数 | median_views ÷ followers | フォロワー極小だと大きくなる |
| last_post_date | YYYY-MM-DD | 最新投稿日（見えた範囲）。YouTubeは「最終投稿からの日数」から逆算 | TikTokは動画IDからの推定で数日ずれ得る |
| retrieved_date | YYYY-MM-DD | 取得日 | |
| source_url | 文字列 | 確認元URL・ツール（tt.py/ttv.py/ig.py/yt-dlp等） | |
| first_frame_text | 文字列 | 1コマ目の文字の有無と実例。YouTubeは「（タイトル）」＋最新タイトルで代用 | 多くは説明文からの推定 |
| opening_type | A商品名紹介 / B買う前の悩み・不一致 / C後から見つける / その他 / 不明 | 冒頭の入り方。A=商品名・サービス名から入る、B=購入/利用前の悩み・不一致から入る、C=後から見つけた・結果から入る。既存行は opening-types-rows.csv のGrok分類を流用、新規行は調査Grokが付与 | 説明文ベースの推定が中心 |
| opening_type_evidence | 文字列 | 判定根拠の短い引用 | |
| face_shown | あり / あり（推定） / なし / 不明 | 本人の顔が映るか | 目視ではなく記述ベースが多い |
| main_subject | 人 / 手元 / 動物 / キャラ / 商品 / 不明 | 主役。調査票の記述で最初に出た主役を1つ採用 | |
| template_fixed | あり / 一部 / なし / 不明 | 毎回同じ型（構成・テロップ・シリーズ）か | |
| duration_sec | 数値 | 見た動画の尺（秒）の中央値 | 代表数本のみ |
| hashtag_count | 数値 | 記載されたハッシュタグ数（調査票に個数があればその値、無ければ記載タグの数）。YouTubeはタイトル1本あたり平均 | 例示タグだけの場合は過小 |
| pr_label | あり / なし / 不明 | #PR・提供・タイアップ等の表記が見た範囲にあるか（YouTubeは概要欄PR表記） | |
| audio | ナレ / トレンド音源 / BGM / オリジナル / 不明 | 音の種類。ナレ=ナレーション・本人の声。オリジナル=「オリジナル楽曲」等の自作音源名。YouTubeは自動字幕あり比率≥50%をナレとした | 音源名からの推定 |
| product_display | 「;」区切り: 使用・実演 / 比較・ランキング / 成分解説 / 価格表示 / レビュー・検証 / なし/未確認 / その他/不明 | 商品の見せ方（キーワード規則で符号化）。`str.contains`で使う | |
| feature_source | 確認済 / 推定（説明文） | 確認済=TikTok動画ページの画面上テキスト等で1コマ目の文字を確認できた行 | 大半は推定 |
| data_origin | 文字列 | 3platform:…=既存調査からの再利用、4genre:<ラン名>=今回の新規Grokラン | |
| notes | 文字列 | 補足（再ラベル、商品の見せ方の原文冒頭など） | |

## videos.csv（1行1動画、ある分だけ）
| 列 | 定義 |
|---|---|
| platform | TikTok / Instagram / YouTube |
| handle | accounts.csv の handle に対応 |
| video_url | 動画URL |
| date | 投稿日（不明なら空） |
| views / likes | 再生数・いいね数（見えた値） |
| duration | 尺（秒） |
| caption_head | タイトル/キャプション冒頭40字 |
| sound | 音源名（分かれば） |
限界: YouTubeは既存調査のShortsタブ直近10本（日付・尺は公開ページを読めた分のみ）。TikTok/Instagramの既存行は動画単位の保存がなく、新規ランの videos.md 分のみ。

## 符号化のルール
- 「不明」は値が見えなかった／判定できなかったもの。集計では分母から除く（report.md の n件中m件は判定可能件数が分母）。
- 数字は丸め表記（1.2万=12,000）を数値化。推測値は入れていない。

## ユーザー参考アカウント
notes が「ユーザー参考アカウント」で始まる4行（美容=@the.care.logic、ドッグフード=@nuts0629、見守りカメラ=@junjun_ranran、婚活=@yako.shiawasekon）。分析時は `d[~d.notes.str.contains('ユーザー参考アカウント', na=False)]` で除外するか、個別比較に使う。
