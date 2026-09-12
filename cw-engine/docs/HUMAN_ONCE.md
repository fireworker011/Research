# 人間が一度だけやること（CW）

日常は Issue にコメントするだけ。Cursor を起こさない。Grok の HQ clone に CW を足さない。

## 一度だけ

1. 非公開リポジトリを作る（済: `fireworker011/cw-work`）
2. GitHubアプリで `cw-work` を開く → 「コード」→ 右上「+」→「Create new file」/「新しいファイルを作成」。
   ファイル名欄に次をそのまま入れる（フォルダは自動でできる）:
   `.github/workflows/cw.yml`
   中身は次のページを開いてコピーし、貼る:
   https://github.com/fireworker011/Research/blob/cursor/cw-auto-commander-c1fb/cw-engine/private-repo/cw.yml
   「Commit」/「コミット」→ main に直接コミット。これで「置く」は終わり。
3. Settings → Actions → General → Workflow permissions を **Read and write**
4. Secrets は任意。`CW_FACTS_JSON`（CW 公開プロフィールにある事実だけ。氏名・年齢は入れない）。完成品は Grok Bot が書くので `ANTHROPIC_API_KEY` は不要
5. Actions で「CW 司令塔」を Run workflow → Issue `CW — 司令塔` が立つ
6. `CW: PROFILE` → 自己PR を（人間が書く）を埋めてクラウドワークスのプロフィールに貼る

## 毎回（1 案件）

| いつ | やる |
|---|---|
| 合う仕事を見つけた | `CW: JOB <id>` + 公開文 |
| 応募稿が出た | （人間が書く）を埋めて送る → `CW: SENT <id>`。送らない → `CW: SKIP <id>` |
| 相手から文 | `CW: MSG <id>` + 文 → 下書きを貼る |
| **受注する** | `CW: CONTRACT <id>` + メモ。断る → `CW: REJECT <id>` |
| 仮払い確認・素材が来た | `CW: MAKE <id>` + 素材 → Grok が書いて `CW: DRAFT <id>` |
| DELIVERY.md を見た | 納品ボタン → `CW: DELIVERED <id>` |
| 修正依頼 | `CW: REVISE <id>` + 依頼文 |
| 報酬確定を画面で見た | `CW: PAID <id> <整数円>` |

## やらなくていい

- Cursor を24時間動かさない。ログインしたかをエージェントに確認させない
- 公開リポジトリ `Research` の Issue に CW を書かない。`Grok Bot — 指示` にも書かない
- 応募を連発しない。下書きが 3 件たまったら新しい JOB を入れない
- 公開の報酬表示を PAID に書かない。conversions.csv（アフィ）に CW を足さない
- 仮払い前に着手しない。LINE 等に移らない。無い実績を書かない
