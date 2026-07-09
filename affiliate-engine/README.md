# Affiliate Engine — 2ヶ月で月利30万円を目指す運用システム

Threads を軸にしたアフィリエイト運用の **投稿 → 計測 → 改善** ループを自動化するシステム。
GitHub Actions で無人運転し、判断（案件選定・ジャンル取捨・成果確認）だけを人間が週次で行う。

> **最初に正直な前提を。** 「2ヶ月で月30万」は *保証ではなく上振れシナリオ* です。
> 新規アカウント発の SNS アフィリエイトで 60 日目に月30万に到達するのは少数派で、
> 典型的な60日目は月数千円〜数万円です。このシステムがやるのは、
> **(1) 到達確率を上げる**（毎日実測データで意思決定する）、
> **(2) 到達しない場合に「何が足りないか」を数字で特定する**、の2つです。
> 何もツールなしで運用するより圧倒的に有利ですが、魔法ではありません。

---

## アーキテクチャ

```
┌────────────────────────────────────────────────────┐
│ strategy-engine.js（週1回、手動 or ローカル）        │
│  Claude でジャンル別テンプレ生成                     │
│  ← output/top_posts.json（実測の勝ちパターン）を     │
│     few-shot として注入 = 週次で型が進化する          │
│  → threads_posting_schedule.csv（60日分）            │
└──────────────┬─────────────────────────────────────┘
               ↓
┌────────────────────────────────────────────────────┐
│ threads-poster.js（GitHub Actions cron 4回/日）      │
│  期日到来分だけ投稿して終了（ステートレス・常駐不要）  │
│  投稿前に compliance.js（#PR自動付与・NG表現ブロック）│
└──────────────┬─────────────────────────────────────┘
               ↓
┌────────────────────────────────────────────────────┐
│ report.js（GitHub Actions 毎日14:00 JST）            │
│  Threads Insights + ASP成果CSV → 日次レポート        │
│  月末着地予測 / 目標との差 / ジャンル別成績           │
│  → top_posts.json（次回テンプレ生成に自動フィード）   │
└────────────────────────────────────────────────────┘

＋ video-semi-auto.js（任意・手動）: 反応が良かった投稿を
  Shorts/Reels 動画化 → 確認 → 公式ツールで予約投稿
＋ shorts-research.js（GitHub Actions 毎朝）: YouTube Shorts チャンネル別に
  Web検索で市場リサーチ → 台本レベルのネタ出し → Issue 配信（半自動）。
  採用分は video-semi-auto.js --ideas で動画化。--select-genre で新チャンネルの
  ジャンル選定リサーチも可（詳細: docs/youtube-shorts-strategy.md）
＋ funnel-calc.js: 目標金額から必要ビュー数を逆算
```

## 元構想（fable5 一式）から変更した点と理由

| 元構想 | 本実装 | 理由 |
|---|---|---|
| Sakura AI が人間のふりをして DM 自動返信 | **実装しない** | 相手を欺く行為であり、Meta 規約違反。発覚時は全アカウント凍結＝収益ゼロ。DM は自分で返す（テンプレ文はテンプレ生成で用意可能） |
| アダルト高単価ジャンル | 転職など合法高単価に置換 | Threads 上の性的訴求は Meta ポリシー違反で BAN 最速コース。転職案件は1件1万円超で単価面の代替になる |
| Claude に「バズアカウント調査」させる | 実測メトリクスの改善ループに置換 | API 経由の Claude は SNS を閲覧できず、架空のアカウント・数値を捏造する。捏造データでの戦略判断は害でしかない |
| node-schedule 常駐プロセス | ステートレス + GitHub Actions cron | PC スリープ・再起動で60日運用は必ず止まる。既存の婚活ワークフローと同じ方式に統一 |
| Threads API 呼び出し | 修正 | 元コードはアクセストークン未送信・公開ステップ欠落で1件も投稿できない状態だった |
| 160本を1回の API 呼び出しで生成 | ジャンル別に分割生成 | max_tokens 4096 では確実に途中で切れて JSON パース失敗する |
| 広告表記なし | #PR 自動付与＋NG表現ブロック | 2023年10月施行のステマ規制（景品表示法）で広告明示は法的義務。美容系の効果断定は薬機法リスク |

## セットアップ

```bash
cd affiliate-engine

# 1. 設定ファイル作成（example をコピーして編集）
cp config/accounts.example.json config/accounts.json
cp config/links.example.json config/links.json
cp config/funnel.example.json config/funnel.json

# 2. テンプレ・スケジュール生成（Claude API キーが必要）
export ANTHROPIC_API_KEY="sk-ant-..."
node src/strategy-engine.js

#    API キーなしの場合はシードテンプレからスケジュールだけ生成できる
node src/strategy-engine.js --from-file data/seed_templates.json

# 3. ドライランで投稿内容を確認（必ずやる）
export THREADS_KONKATSU_USER_ID="..."
export THREADS_KONKATSU_ACCESS_TOKEN="..."
node src/threads-poster.js --dry-run

# 4. 生成された CSV をコミットして push すれば、
#    GitHub Actions（affiliate_engine_post.yml）が自動投稿を開始
git add output/threads_posting_schedule.csv output/strategy_data.json config
git commit -m "feat: 投稿スケジュール更新" && git push
```

GitHub Secrets には各アカウントの `THREADS_*_USER_ID` / `THREADS_*_ACCESS_TOKEN` を登録
（既存の `THREADS_KONKATSU_*` はそのまま使える）。

長期トークンは60日で失効するため、`refresh_threads_token.yml`（毎週月曜 09:07 JST）が
5アカウント分を自動リフレッシュする。**Secrets への書き戻しまで完全自動化するには、
Secrets 書き換え権限を持つ Fine-grained PAT を `GH_SECRETS_PAT` として登録する**
（GitHub の仕様上、Actions の既定トークンでは Secrets を書き換えられないため）:

1. GitHub → 右上アイコン → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token
2. Repository access: Only select repositories → このリポジトリを選択
3. Permissions → Repository permissions → **Secrets: Read and write**（他は不要）
4. 有効期限は最長（1年）にし、生成されたトークンをリポジトリの Secrets に `GH_SECRETS_PAT` として登録
5. PAT 自体の期限が切れたら同じ手順で再発行（切れている間は Issue 通知のフォールバックに自動で戻るだけで、投稿は止まらない）

`GH_SECRETS_PAT` 未設定の間は、新トークンが実行ログの Summary に出力され
更新依頼の Issue が自動作成されるので、手動で Secrets に貼り直す。

## 運用ルーチン（完全自動化後）

| 頻度 | 作業 | 所要時間 |
|---|---|---|
| 自動 | 投稿（4回/日・実行ごとに順序と間隔を分散）・KPIレポート（毎日14時） | 0分 |
| 自動（毎日06:00） | デイリー自動改善: 実測分析 × Web検索市場リサーチ → テンプレ草案を自動反映（実測ワースト3本引退・ジャンル36本上限）→ スケジュール再生成 → エンゲージ素材生成 | 0分 |
| **毎日（唯一の人間の仕事）** | GitHub Issue「📋 デイリー・エンゲージメントキット」に届く返信・コメント下書きをアプリからコピペ送信。ついでに周辺投稿へいいね10〜20件（コメントした相手はフォローもする） | **10分** |
| 自動（毎朝06:00前後） | YouTube Shorts 市場リサーチ&ネタ出し: チャンネル別の台本ネタを Issue「🎬 YouTube Shorts ネタ出しキット」に配信 | 0分 |
| 週1 | ASP 管理画面から成果を `data/conversions.csv` にエクスポート（リンク解禁後） | 10分 |
| 週2-3（任意） | ネタ出しキットから採用分を `video-semi-auto.js --ideas` で動画化 → YouTube Studio で予約投稿。Threads 反応上位の動画化（`--date` 指定）も同コマンド | 30分 |

### フェーズ設計

- **認知フェーズ（`config/accounts.json` の `awareness_until` まで）**: 全投稿が価値提供のみ。リンク付きテンプレはスケジュール生成と投稿時の両方で自動除外。フォロワー獲得に専念
- **収益フェーズ（awareness_until 以降）**: `config/links.json` にリンクを入れておけば、解禁日から自動でリンク付き投稿が混ざり始める（追加作業なし）
- 新規アカウントは `created` から 1週目1本/日 → 2週目2本/日 → 3週目〜3本/日 に自動ランプアップ（急稼働はスパム判定・リーチ抑制の要因）

### いいね・フォロー・リプの自動化をしない理由（重要）

- いいね・フォローの API は公式に存在しない。自動化するには非公式ツール（画面操作の自動化等）しかなく、これは Meta が最も積極的に検知・凍結している行為。「ランダム間隔で人間らしく」を謳うツールでも、検知は挙動パターンだけでなく端末・ネットワーク指紋でも行われており、新規アカウントほど閾値が低い。5アカウント全凍結＝事業終了のリスクに見合わない
- 返信の自動送信は技術的には可能だが、人間のふりをする欺瞞になるため行わない。代わりに**下書きを毎朝全部 AI が用意する**（`src/engage.js` → `output/engage/` に保存 + GitHub Issue にコメント投稿）。スマホでファイルを開く手間を省くため、Issue へのコメントとして通知が届く設計にしている。送信だけ人間がやる設計が、凍結リスクゼロで得られる実質的な自動化の上限
- 投稿の分散（実行ごとの順序シャッフル・間隔ランダム化）は行う。これは検知回避ではなく、複数アカウント同時刻一斉投稿というスパム的挙動そのものを避けるための設計

## 2ヶ月ロードマップ（現実的な数字で）

まず `node src/funnel-calc.js` を実行して、目標に必要な数字を体感すること。
基準シナリオ（単価¥5,000・承認率80%・CVR1.5%・CTR0.8%）で月30万に必要なのは:

- 成約 **75件/月** ← クリック **5,000回/月** ← ビュー **62.5万回/月 ≒ 2.1万回/日**
- 5アカ×3投稿/日なら **平均 1,400 views/投稿**、3アカなら **2,300 views/投稿**

新規アカウントの初期は 1投稿あたり数十〜数百 views が普通。つまり勝負は
「上振れする型をどれだけ早く見つけて全アカウントに横展開するか」で決まる。

| 期間 | やること | 撤退・転換ライン |
|---|---|---|
| **Week 1** | 1アカウント（婚活=既存）で本稼働開始。プロフィール・固定投稿整備。ASP 提携申請（単価1万円超の転職案件を必ず含める）。短縮URL 設定 | — |
| **Week 2-3** | 2〜3アカウントに拡大（各アカウントは独立したテーマで正規運用）。全ジャンル均等に投稿しデータ収集 | 平均views/投稿が全体の半分未満のジャンル → テンプレ再生成 |
| **Week 4** | 初回の大選別。ワースト1ジャンル停止、ベストジャンルに枠を再配分。反応上位投稿を Reels/Shorts に展開開始 | CTR（短縮URL実測）が 0.3% 未満 → CTA の書き方を全面見直し |
| **Day 30** | 中間評価。現実的な良ライン: 確定 ¥30,000 | **確定 ¥10,000 未満なら案件（オファー）自体を総入れ替え**。ジャンルではなく案件が原因のことが多い |
| **Week 5-7** | 増幅期。勝ち型に集中、単価の高い案件に導線を寄せる。フォロワーが付いたアカウントは投稿数を+1 | 特定アカウントのリーチが急落 → 数日投稿を減らして回復を待つ（シャドウバン兆候） |
| **Day 60** | 最終評価。¥100k 超えていれば、同じ改善ループの継続で ¥300k は射程内。¥300k は最良ケース | ¥30k 未満 → プラットフォーム or 商材の根本転換を検討 |

**加速レバー（効果が大きい順）**: ①高単価案件への比重（単価2倍は必要ビュー半分）
②勝ち投稿の Reels/Shorts 横展開（Threads 外から流入）③DM・リプの丁寧な手動対応（CVRに直結）

## コンプライアンス（＝アカウント生存戦略）

BAN・行政指導は収益ゼロに直結するため、以下はシステムで強制している:

- **ステマ規制（景表法・2023年10月〜）**: リンク付き投稿に `#PR` を自動付与。外すと投稿主（あなた）が措置命令の対象になり得る
- **薬機法/誇大表現**: 「絶対痩せる」「必ず稼げる」等は `compliance.js` が投稿前にブロック
- **Meta ポリシー**: アダルト・出会い系訴求の NG ワードをブロック。API 投稿は公式 Threads API のみ使用（1アカウント250投稿/日の公式上限に対し、デフォルト10/日と大幅マージン）
- **やらないこと**: 人間を装う自動 DM、フォロー/いいねの自動化、同一内容の複数アカウント同時投稿（スパム判定要因）

各 ASP のオファーごとに「SNS 投稿可否」の規約が異なるので、提携時に必ず確認すること。

## ファイル構成

```
affiliate-engine/
├── src/
│   ├── strategy-engine.js   # テンプレ・スケジュール生成（Claude）
│   ├── threads-poster.js    # 自動投稿（ステートレス）
│   ├── report.js            # KPI収集・日次レポート・top_posts 抽出
│   ├── insight.js           # 実測×Web検索リサーチ → 改善レポート+テンプレ草案
│   ├── apply-proposals.js   # 草案の統合・引退・スケジュール再生成（--auto で無人運転）
│   ├── engage.js            # 返信・コメント下書きの自動生成（毎朝のコピペ10分用）
│   ├── shorts-research.js   # YouTube Shorts 市場リサーチ&ネタ出し（半自動・毎朝）
│   ├── funnel-calc.js       # 目標→必要数値の逆算
│   ├── video-semi-auto.js   # Shorts/Reels 動画生成（要 ffmpeg + Noto CJK、--ideas でネタから生成）
│   ├── compliance.js        # #PR付与・NG表現ブロック
│   ├── claude-client.js     # Claude API（リトライ・JSON抽出）
│   └── util.js              # CSV/JSON/日付ユーティリティ
├── config/                  # accounts / links / funnel / youtube（example をコピー）
├── data/conversions.csv     # ASP成果の手動エクスポート（週1更新）
├── docs/youtube-shorts-strategy.md  # Shorts 第三弾の戦略・ジャンル選定
└── output/                  # スケジュールCSV・状態・ログ・レポート・engage/shorts素材

.github/workflows/
├── affiliate_engine_post.yml     # 自動投稿（JST 7/12/19/21時・分散付き）
├── affiliate_engine_report.yml   # 日次レポート（JST 14時）
├── affiliate_engine_insight.yml  # デイリー自動改善+エンゲージ素材（JST 6時）
└── affiliate_engine_shorts.yml   # Shorts 市場リサーチ&ネタ出し（JST 6時前後・Issue配信）
```

依存パッケージなし（Node.js 20+ のみ）。`npm install` 不要。
