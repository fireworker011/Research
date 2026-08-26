# 動画パイプライン — 指示書との対応

指示書の「不足情報は補完しない」に従い、リポジトリと公式ヘルプで確認できたことだけを動かしている。

## ディレクトリ

```
affiliate-engine/
├── config/video-pipeline.json     # 尺・間隔・48h。基準値は null。generation_enabled は false
├── data/video/
│   ├── genres.csv                 # 9ジャンル。accounts.json とキー・名前が一致必須
│   ├── packets.csv                # 出した指示書
│   ├── posts.csv                  # 人間が書いた公開記録
│   ├── views.csv                  # 人間が書いた視聴回数
│   └── deletions.csv              # 人間が削除したあとだけ書く
├── prompts/grokbot-instruction.md # Grokbot 指示書の最終テンプレート
├── src/video-pipeline.js          # スケジュール / emit / 48h レビュー
└── output/video/pipeline/         # 生成物（指示書ファイル・レビュー）
```

## 指示書 → 実装

| 要求 | 実装 | 根拠 |
|---|---|---|
| 9ジャンル | `data/video/genres.csv`（accounts.json と照合） | ジャンル名は既存定義 |
| 30分間隔で Grokbot に渡す | 同日の有効ジャンルを 30 分ずらす。1実行1パケット | 同時実行防止は指示書の文言 |
| 各ジャンル 2日に1回 | `(epochDay + genreIndex) % 2 === 0` | 日付決定論。巡回カーソル禁止 |
| 30〜60秒 | config の duration | 指示書の文言 |
| 市場の型をリサーチして模倣 | テンプレに構造の学習を書く。映像・台本のコピーは禁止 | video-cash-loop |
| Grok Imagine で動画 | テンプレに書く。API は呼ばない | 仕様がリポジトリに無い |
| 3媒体へ自動投稿 | `--post` は終了コード 2。媒体は YouTube のみ enabled | 投稿 API 未確認。同時立ち上げ禁止。Shorts の URL はクリック不可 |
| 全投稿にアフィリンク | Shorts はプロフィール CTA。links.json は空 | 公式ヘルプ + 既存ファイル |
| 48時間後に視聴回数 | `views.csv` を読む。数字が無ければ `needs_views` | 発明しない |
| 基準値未満は自動削除 | 基準値 null の間は `needs_threshold`。`--delete` は終了コード 2 | 数値が指示書に無い |
| 削除を次回プロンプトへ | `deletions.csv` をテンプレのフィードバック欄へ | 記録がある分だけ |

## 確認待ち（ここが埋まるまで推測でコードを足さない）

1. Grokbot の呼び出し方法（ファイル手渡し / Cursor agent / HTTP）。リポジトリに仕様なし。
2. 48時間後の視聴回数の基準値。`view_threshold_48h` は null。
3. 1日のスロット開始時刻。未指定のため JST `00:00` 起算（`slot_start_jst`）。
4. 9ジャンルすべてを動画化するか。現在 `video_enabled` はペットだけ。
5. Instagram / TikTok の公式投稿 API と、リンクを置ける場所。
6. 自動削除を API でやるか、候補を人間が消すか。
7. Grok Imagine agent の実体（xAI API / 別エージェント / 手作業）。

## 動かし方

```bash
cd affiliate-engine
node src/video-pipeline.js --self-test
node src/video-pipeline.js --schedule --dry-run
node src/video-pipeline.js --emit --review --dry-run
```

`generation_enabled` が false のあいだ、emit は指示書ファイルを書かない。14日実験中（2026-08-22 起算）も `skip_experiment`。

公開したら `posts.csv` に `published_at` を書く。48時間後に YouTube スタジオの数字を `views.csv` へ。レビューが `delete_candidate` でも API では消さない。消したなら `deletions.csv`。
