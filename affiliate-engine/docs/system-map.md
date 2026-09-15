# 現状の仕組み（2026-08-26 時点のリポジトリ事実）

推測で足した部品は書いていない。ソースは `config/accounts.json`、`src/`、`.github/workflows/`、`docs/video-cash-loop.md`。

## 動いているもの

```
strategy-engine.js  →  threads_posting_schedule.csv（日付決定論）
        ↓
threads-poster.js   →  Threads へ期日到来分だけ投稿（GitHub Actions 毎時）
        ↓
amplify.js          →  500ビュー超の投稿へリンクリプライ（1アカ2回/日）
        ↓
report.js           →  日次 KPI
insight.js          →  Threads テンプレの改善（YouTube には使わない）

video-judge.js      →  YouTube は判定だけ。投稿しない。数字を発明しない
video-semi-auto.js  →  テロップ動画の半自動。アップロードは公式ツール
video-pipeline.js   →  Grokbot 指示書ファイルと 48h レビュー。投稿・削除・API 呼び出しなし
```

## 9ジャンル（すでに決まっている）

`config/accounts.json` の順:

| key | ジャンル | 動画 |
|---|---|---|
| konkatsu | 婚活 | 対象外 |
| sidejob | 副業 | 対象外 |
| beauty | 美容 | 対象外 |
| bodymake | 筋トレ | 対象外 |
| education | 教育 | 対象外 |
| setsuyaku | 節約 | 対象外 |
| tenshoku | 転職 | 対象外 |
| pet | ペット | YouTube `@pet_story_select` のみ（14日実験中） |
| sleep | 睡眠 | 対象外 |

「9種類のジャンル名はすでに決まっていますか」への答えは **はい**。上表がソース。動画チャンネルが確認できているのはペットだけ。

## 媒体

| 媒体 | Threads 自動投稿 | 動画 |
|---|---|---|
| Threads | あり（公式 API） | 使わない |
| YouTube Shorts | なし | 人間が投稿。判定は `video-judge.js` |
| Instagram Reels | なし | キューまで。実験中は足さない |
| TikTok | なし | 未接続。実験中は足さない |

## 動画の数字（発明していない）

`data/video_cash_log.csv` にある行だけを `video-judge.js` が見る。

2026-08-26 の判定: 実験 5/14 日目 `CONTINUE_EXPERIMENT`。記録行は 2026-08-22 の1行。直近7日の投稿/再生/クリック/成果は CSV 上 0。

ゲート（`video-judge.js` の定数。視聴回数の削除基準ではない）:

- 週15クリックで導線
- 累計50クリック + 成果0 で案件疑い
- 週50クリックが3週で月100万の会話解禁

## リンク

`config/links.json` の値はすべて空。Threads は空キーのテンプレを投稿時スキップする。

YouTube Shorts の説明欄・コメントの URL はクリック不可（[YouTube Help](https://support.google.com/youtube/answer/13748639)）。導線は `詳しくはプロフィールのリンク（PR）`。

## 指示書との差分

詳細は `docs/video-pipeline.md`。実装したのは、確認済みのジャンル・尺・間隔・48時間レビューと、Grokbot へ渡す指示書ファイル。実装していないのは、未確認の投稿 API、削除基準値、Grokbot の HTTP 仕様、3媒体の同時投稿。
