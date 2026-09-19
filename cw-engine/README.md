# CW Engine — クラウドワークス受注パイプライン（側線）

**取込・資格判定・応募稿・定型返信・BRIEF・QA・台帳はコード。応募と完成品は既存 Grok Bot。人間は契約・外部案内誘導・納品。**
Affiliate / XM と同じく GitHub 上で保守する。ただし **実行と保存は人間の非公開リポジトリ**（公開リポジトリには守秘物を置けない）。

> **最初に正直な前提を。** クラウドワークスに公式の応募 REST API は無い。**このエンジン（Actions）は会員ページに入って応募しない。** 応募は既存 Grok Bot「CW受注」。人間は契約・外部サイトの案内誘導・納品ボタン。
> 総統括の命令により、100万本線（`hq-instruct.js` / `G_hq_boot.txt` / `MACHINE.md`）は触らない。**この PR をマージしなくても動く。**

| 知りたいこと | ファイル |
|---|---|
| 地図（今組んだもの / 組まないもの） | [`docs/AUTO.md`](docs/AUTO.md) |
| Bot 役ごとの指示（全部） | [`docs/BOTS.md`](docs/BOTS.md) |
| 役の数 | [`docs/AGENTS.md`](docs/AGENTS.md) |
| 懸念と解決 | [`docs/CONCERNS.md`](docs/CONCERNS.md) |
| 状態と成果物 | [`docs/PIPELINE.md`](docs/PIPELINE.md) |
| コマンド | [`docs/COMMANDS.md`](docs/COMMANDS.md) |
| 定型文 | [`docs/TEMPLATES.md`](docs/TEMPLATES.md) |
| 人間が一度だけ / 毎回 | [`docs/HUMAN_ONCE.md`](docs/HUMAN_ONCE.md) |
| 非公開リポジトリの作り方 | [`private-repo/README.md`](private-repo/README.md) / [`private-repo/cw.yml`](private-repo/cw.yml) |
| Grok 前面（既存 Bot。HQ clone には足すな） | [`docs/grok-bots/ROSTER.md`](docs/grok-bots/ROSTER.md) / [`G_cw.txt`](docs/grok-bots/G_cw.txt) |

```
ナオミチ ── Issue「CW — 司令塔」（非公開リポジトリ）にコメント ──▶ GitHub Actions（非公開）
                                                                      │ checkout: Research/cw-engine（公開・読むだけ）
                                                                      ▼
   intake → qualify → apply-draft → reply-draft → brief → make(prompt) → Grok DRAFT → compliance(QA) → deliver → ledger
                                                                      │
                                                                      ▼
                                              cw-apply: / cw-reply: / cw-brief: / cw-make: / cw-deliver: / cw-desk:（next_human）
ナオミチ ── 契約・外部案内誘導・納品ボタン・出金 ──▶ CW: CONTRACT / DELIVERED / PAID
Grok ── 探す・応募・返信・完成品 ──▶ CW: JOB / SENT / MSG / MAKE / DRAFT
```

## 主力（AI で完結するもの）

`config/capability.json` の `ai_complete: true`: 記事・SNS投稿文・動画台本・商品説明／コピー・整文／要約・翻訳・表／CSV 整理。
素材支給の短尺動画編集は「編集計画」まで（主力ではない）。

## 検証

```bash
cd cw-engine
node src/self-test.js                                   # LLM なし・トークンなしで全経路
node src/apply-commander-comment.js --dry-run --comment "CW: DESK"
```

## 不変条件

`.cursor/rules/cw-engine.mdc` が正。要点: 本線を触らない／守秘物は公開に置かない／送信と受注可否は人間／LLM に選ばせない／実績と円を発明しない／仮払い前に着手しない／Grok clone を増やさない。
