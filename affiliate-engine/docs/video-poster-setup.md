# 動画投稿エンジン（YouTube Shorts / TikTok / Instagram Reels）セットアップ

`src/video-poster.js` は `threads-poster.js` の設計を動画に移したもの。
常駐しない。起動時に期日が来た未投稿分だけ投稿して終了する。

**アカウントは人間が手動で開設する。** このエンジンはアカウントを作らない（各媒体の規約違反・凍結の巻き添え）。
開設済みアカウントを `video-oauth.js` で OAuth 登録し、トークンを GitHub Secrets に置くと投稿できる。

## 投稿されるまでの関門（全部通らないと出ない）

| # | 関門 | どこで決まる | 落ちたときの state |
|---|---|---|---|
| 1 | キューに期日到来の未投稿がある | `output/video_queue.jsonl` + `CATCHUP_HOURS`（既定6h） | （対象外） |
| 2 | アカウントが `enabled` で platform 対応 | `config/video_accounts.json` | （ログのみ） |
| 3 | **video-judge のゲートが開いている** | `output/video/latest.json` の `posting.allowed`。判定が2日以上古い・無い・旧形式なら閉 | `skipped_judge` |
| 4 | その媒体がゲートに載っている | `posting.platforms` = 判定 × `platform_unlock`（人間が書いた日付） | `skipped_platform_gate` |
| 5 | 週次上限 `posting.weekly_cap` 未達 | state の直近7日成功数（アカウント別） | （ログのみ） |
| 6 | デイリー上限 `daily_cap` 未達 | `video_accounts.json`（既定1） | （ログのみ） |
| 7 | 30日以内に同じ動画/本文を出していない | state の `recent` | `skipped_duplicate` |
| 8 | 検品: URL なし・`#PR` あり・プレースホルダーなし・長さ/タグ数・`compliance.checkContent` | `buildCaption()` | `blocked` |
| 9 | 動画がある（ローカル or `video_url`） | キュー行 | （ログのみ） |
| 10 | **ライブゲート**: `live_enabled: true` かつ env `VIDEO_POST_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK` | config + workflow 入力 | どちらか欠けると全件ドライラン |
| 11 | Secrets が揃っている | 各 `*_env` | （ログのみ） |

ドライランでは state を書かない（threads-poster と同じ）。

## 1. 媒体を開ける（人間の決定）

`config/video_accounts.json` の `platform_unlock` に日付を書く。null の媒体はゲートに載らず、判定が何であれ投稿しない。

```json
"platform_unlock": { "youtube": "2026-06-20", "tiktok": null, "instagram": null }
```

`docs/video-cash-loop.md` の原則どおり、同時に2媒体を開けない。実験（14日）中は YouTube のみ。

## 2. アプリを作る（各媒体1回・人間）

| 媒体 | 場所 | 作るもの | スコープ | 注意 |
|---|---|---|---|---|
| YouTube | Google Cloud Console | YouTube Data API v3 有効化 → OAuth クライアント ID | `youtube.upload` | 同意画面を**本番**にする。テストのままだと refresh_token が7日で失効。アップロードは1本 1600 クォータ（1日 10,000） |
| TikTok | TikTok for Developers | アプリ → Login Kit + Content Posting API | `video.publish` | 審査前は `SELF_ONLY`（本人のみ公開）しか選べない。リダイレクト URI は https 必須 |
| Instagram | Meta for Developers | アプリ → 「Instagram API with Instagram Login」 | `instagram_business_basic`, `instagram_business_content_publish` | 投稿先はプロアカウントのみ。動画は**公開 https URL** から Meta が取得（ファイル送信不可） |

## 3. アカウントを OAuth 登録する（ローカルで1回）

```bash
cd affiliate-engine
# YouTube（localhost で code を受ける。コンソールに http://localhost:8787/callback を登録）
node src/video-oauth.js youtube --account pet_youtube --client-id ID --client-secret SECRET --listen 8787

# TikTok / Instagram（https のリダイレクト先が必要。許可後の URL を貼る）
node src/video-oauth.js tiktok    --account pet_tiktok    --client-key KEY --client-secret SECRET --redirect-uri https://example.com/cb
node src/video-oauth.js instagram --account pet_instagram --app-id ID   --app-secret SECRET   --redirect-uri https://example.com/cb
```

出力された `NAME=value` を GitHub Secrets に登録する。ファイル・チャット・Issue に貼らない。
`--account` を付けると `video_accounts.json` の `*_env` 名で出るので、そのまま貼れる。

Secrets 名は workflow の `env:` にも並べる（`affiliate_engine_video_post.yml` / `affiliate_engine_video_token_refresh.yml`）。
アカウントを足すときは config + 2つの workflow の3箇所。

## 4. キューに動画を積む

```bash
node src/video-poster.js --enqueue --account pet_youtube \
  --video affiliate-engine/assets/video/pet_001.mp4 \
  --title "猫が夜中に走る理由" \
  --desc "猫が夜中に走るのは狩りの名残\n3つの説を整理した" \
  --date 2026-09-12 --time 07:00 --template-id pet_001
```

- `--video` は リポジトリ相対パス（コミット済み）か https URL。`output/videos/` は gitignore なので Actions からは見えない
- Instagram は https URL が必須。ローカルパスの場合は `public_base_url` + ファイル名で組み立てる
- `{{AFFILIATE_LINK}}` は消される。本文に URL は書けない（書くと `blocked`）。導線は「詳しくはプロフィールのリンク（PR）」の1回だけ
- `#PR` が無ければ自動で付く

キューは `output/video_queue.jsonl`（1行1件）。GitHub アプリから直接編集してもよい。

## 5. 実行

```bash
node src/video-poster.js --dry-run     # いつでも安全
node src/video-poster.js               # live_enabled + VIDEO_POST_LIVE_CONFIRM が揃っていれば実投稿
node src/video-poster.js --self-test
node src/video-poster.js --refresh-tokens
```

GitHub Actions: `affiliate_engine_video_post.yml` を **手動起動**（schedule は付けない。`affiliate_yaml_guard.yml` が守る）。
`dry_run=false` と `live_confirm=I_UNDERSTAND_THE_RISK` を両方入れ、かつ config の `live_enabled` が true のときだけ投稿する。

## 6. 記録（毎日・人間）

`data/video_cash_log.csv` に媒体別に1行。`platform` 列は `youtube` / `tiktok` / `instagram`（空なら youtube）。

```
date,platform,videos_published,views,a8_clicks,conversions,note
2026-09-12,youtube,1,800,3,0,
2026-09-12,tiktok,1,300,0,0,
```

`video-judge.js` が合計でゲートを決め、媒体別の数字を `TODAY.md` に並べる。数字が無い日は投稿されない（`RECORD_MISSING` は閉）。

## 7. トークンの寿命

| 媒体 | 寿命 | 延命 |
|---|---|---|
| YouTube refresh_token | 失効しない（本番同意画面・6ヶ月未使用でなければ） | 不要 |
| TikTok refresh_token | 365日。access_token は24時間（実行ごとに交換） | 週次 workflow が回転分を Secrets へ書き戻す |
| Instagram 長期トークン | 60日 | 週次 workflow が `refresh_access_token` で延命 |

`GH_SECRETS_PAT` があれば自動書き戻し。無ければ Step Summary に新トークンが出るので手動更新（Threads の refresh と同じ運用）。

## やらないこと

- アカウントの自動作成・認証の自動突破・IP 偽装
- 本文・コメント・説明欄へのアフィ URL
- ゲートが閉じている日の投稿、`platform_unlock` に無い媒体への投稿
- 判定の発明（poster は `latest.json` を読むだけ。無ければ閉）
- 同時に2媒体を開けること
