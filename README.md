# SNS運用 15系統システム

3 SNS × 5ジャンル = **15系統**。各系統は専用フォルダの `SYSTEM.md` を持つ。
**1系統 = 1会話 = 1md** で運用する。共通ルールは [`CLAUDE.md`](./CLAUDE.md)。

---

## 使い方(スマホ)
1. 新しい会話を作る
2. 対象系統の `SYSTEM.md` の「起動コマンド」1行を貼る
3. 作業 → 終了時にClaudeが知見を `SYSTEM.md` に追記してcommit

---

## 系統一覧(15系統)

| SNS | 種別 | ニッチ | フォルダ |
|---|---|---|---|
| Threads | 📱スマホ | 転職 | `threads/phone/01_転職` |
| Threads | 📱スマホ | 金融 | `threads/phone/02_金融` |
| Threads | 💻PC | 美容 | `threads/pc/03_美容` |
| Threads | 💻PC | VOD | `threads/pc/04_VOD` |
| Threads | 💻PC | 子育て | `threads/pc/05_子育て` |
| Shorts | 📱スマホ | 転職 | `shorts/phone/01_転職` |
| Shorts | 📱スマホ | 金融 | `shorts/phone/02_金融` |
| Shorts | 💻PC | 美容 | `shorts/pc/03_美容` |
| Shorts | 💻PC | VOD | `shorts/pc/04_VOD` |
| Shorts | 💻PC | 子育て | `shorts/pc/05_子育て` |
| TikTok | 📱スマホ | 転職 | `tiktok/phone/01_転職` |
| TikTok | 📱スマホ | 金融 | `tiktok/phone/02_金融` |
| TikTok | 💻PC | 美容 | `tiktok/pc/03_美容` |
| TikTok | 💻PC | VOD | `tiktok/pc/04_VOD` |
| TikTok | 💻PC | 子育て | `tiktok/pc/05_子育て` |

---

## 週次運用カレンダー

**設計思想: 同じニッチを同じ日にまとめる → リサーチ・ネタ仕込みを1回で3SNS分に使い回せる**

| 曜日 | ニッチ | 系統 | 種別 | 作業場所 |
|---|---|---|---|---|
| **月** | 転職 | Threads転職 / Shorts転職 / TikTok転職 | 📱スマホ | スマホ |
| **火** | 金融 | Threads金融 / Shorts金融 / TikTok金融 | 📱スマホ | スマホ |
| **水** | 美容 | Threads美容 / Shorts美容 / TikTok美容 | 💻PC | PC |
| **木** | VOD | Threads VOD / Shorts VOD / TikTok VOD | 💻PC | PC |
| **金** | 子育て | Threads子育て / Shorts子育て / TikTok子育て | 💻PC | PC |
| **土** | 予備 | バズ投稿の横展開 / 差し込み投稿 | どちらでも | どちらでも |
| **日** | 見直し | 改善ログ確認 / 翌週ネタ仕込み / 週次commitまとめ | - | - |

### 運用のポイント

- **月・火(スマホの日)**: 移動中・すき間時間でOK。会話を開いて起動コマンド1行貼るだけ。
- **水〜金(PCの日)**: Colabで動画・画像生成。パラメータ実績は必ずSYSTEM.mdに書き戻す。
- **土(予備)**: 伸びた投稿を他SNSに横展開する日。例: Threadsで伸びたネタ→そのままShortsの台本に。
- **日(見直し)**: 週の成果(いいね・CV・保存)をメモし、翌週のネタを決めるだけでよい。

### 1日の流れ(スマホの日・例: 月曜=転職)

```
① Threads転職/SYSTEM.md を読んで 起動コマンドを貼る → 投稿文生成 → コピペ投稿
② Shorts転職/SYSTEM.md を読んで 起動コマンドを貼る → 台本生成 → 撮影/編集 → 投稿
③ TikTok転職/SYSTEM.md を読んで 起動コマンドを貼る → 台本生成 → 撮影/編集 → 投稿
```

### 1日の流れ(PCの日・例: 水曜=美容)

```
① Colab で wan22_i2v / Lora_Trainer を起動
② tiktok/pc/03_美容/SYSTEM.md を読んで 起動コマンドを貼る → 素材指示+台本生成
③ 生成完了後パラメータ実績をSYSTEM.mdに追記 → commit
④ Shorts/Threadsの美容も同様に処理(素材を使い回せる)
```

---

## PC系パラメータ管理ルール

Colabノートブック(`wan22_i2v_lightx2v_colab.ipynb` / `Lora_Trainer_XL.ipynb`)の
パラメータは**実際に動かした後、その系統のSYSTEM.mdの「既定パラメータ」欄に追記する**。
机上では決まらないので、初回は空欄のまま実行→結果と設定値をメモして埋めていく。
