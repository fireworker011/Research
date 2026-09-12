# Bot 役への指示（全部。ここが正）

CW 全自動受注は **5 役**。増やさない。各役の指示は下の枠をそのまま使う。

| 役 | 実体 | 常時？ | 触ってよい場所 |
|---|---|---|---|
| 0. 総統括 | Cursor「１００万円売り上げ自動化」 | 起こされた日だけ | 本線。CW は側線として可否だけ |
| 1. CW 司令塔（機械） | 非公開リポジトリの GitHub Actions（`private-repo/cw.yml`）が `cw-engine/src/apply-commander-comment.js` を回す | イベント駆動（人間のコメント） | 非公開リポジトリの Issue `CW — 司令塔` と同リポジトリのファイル |
| 2. CW 前面（任意） | Grok Bot の **別会話**（`docs/grok-bots/G_cw.txt`） | 人間が開いたとき | 告知を写す。完成品は `CW: DRAFT`。HQ clone には足さない |
| 3. CW 総責任者 | Cursor（この PR の作者） | `参謀へ:` で起こされた日だけ | `cw-engine/**` と CI。本線は触らない |
| 4. ナオミチ | 人間 | 外部サイトのクリックと受注可否 | クラウドワークス、非公開リポジトリの Issue と Secret |

HQ の Grok clone（`G_hq_boot.txt`）は **触らない**。CW をそこに足さない。

---

## 0. 総統括への報告（CW 総責任者 → 総統括）

```
CW は側線として自立させた。hq-instruct.js / G_hq_boot.txt / MACHINE.md / handover は触っていない。
実行と保存は人間の非公開リポジトリ。公開リポジトリには cw-engine のコードと CI だけ。
#122 をマージしなくても動く（ENGINE_REF を枝に向ける）。マージの可否は総統括。
CW の円は cw_ledger.csv。approved_yen（アフィ）には足さない。100万本線の分母にしない。
```

## 1. CW 司令塔（機械）への指示 = 仕様

Issue `CW — 司令塔` の人間コメントを 1 通ずつ処理し、`cw-<kind>: <id>` で始まる告知を 1 通返す。末尾に `cw-desk:` のデスク行（`next_human:` を含む）。

| 人間の行 | 機械がやること | 告知 |
|---|---|---|
| `CW: JOB <id>` + 公開文 | 公開文を解析（本文が無ければ公開ページを1回読む）→ 資格判定 → 応募稿（事実カードで埋め、無い項目は（人間が書く））→ `jobs/<id>/JOB.md` `APPLY.md` | `cw-apply:`（落ちたら `cw-desk:` に理由） |
| `CW: SENT <id>` | 状態 sent | `cw-note:` |
| `CW: SKIP <id>` | 状態 skipped | `cw-note:` |
| `CW: MSG <id>` + 相手の文 | 意図分類 → 定型返信の下書き → `messages/` | `cw-reply:` |
| `CW: CONTRACT <id>` + メモ | 状態 contracted → BRIEF（成果物定義・受入条件・手順・不足素材と依頼文）→ `BRIEF.md` | `cw-brief:` |
| `CW: MATERIAL <id>` + 素材 | `materials/NN.md` に保存 | `cw-note:` |
| `CW: MAKE <id>` (+素材) | Grok 用プロンプト（Anthropic は使わない） | `cw-make:` |
| `CW: DRAFT <id>` + 本文 | Grok / 人間の完成品 → QA。合格なら `deliverables/vN/` + `DELIVERY.md` | `cw-deliver:` / 不合格 `cw-qa:` |
| `CW: REVISE <id>` + 修正依頼 | 反映版のプロンプト → また `CW: DRAFT` | `cw-make:` |
| `CW: DELIVERED <id>` | 状態 delivered | `cw-note:` |
| `CW: PAID <id> <整数円> <メモ>` | 台帳 `data/cw_ledger.csv`（カンマ・カタログ・URL は拒否）→ 状態 paid | `cw-note:` |
| `CW: REJECT <id>` | 状態 lost | `cw-note:` |
| `CW: PROFILE` | 自己PR 下書き `profile/PROFILE.md` | `cw-profile:` |
| `CW: HALT` / `CW: PAPER_ONLY` | commander | `cw-desk:` |
| `CW: DESK` | デスクだけ | `cw-desk:` |

やらない: ログイン、応募 POST、`RESUME`、円の発明、素材に無い事実、公開リポジトリへの書き込み、HQ Issue への書き込み。
`ANTHROPIC_API_KEY` は不要。`CW: MAKE` はプロンプトだけ出す。完成品は Grok Bot（別会話）が書いて `CW: DRAFT`。発明しない。QA は機械。

## 2. CW 前面（Grok・任意）への指示

貼るのは `docs/grok-bots/G_cw.txt` の本文だけ。**HQ clone とは別の会話**。要点:

```
機械の告知（cw-*:）を人間に写す。next_human の1行を言う。応募稿は変えずに写す。
`cw-make:` が来たら完成品を書いて `CW: DRAFT <id>` で Issue に貼る。Anthropic は使わない。
仕事 ID を自分で足すな。応募稿を自分で作るな。PAID を代筆するな。ログインするな。remain / n10 を開けるな。
```

非公開リポジトリを Grok が読めないなら、人間が `cw-make:` のプロンプトを Grok に貼り、返ってきた本文を Issue へ `CW: DRAFT` で載せる。HQ clone にこの dump を足すな。

## 3. CW 総責任者（Cursor）への指示

起きる条件は `参謀へ:` の1行だけ。例:

```
参謀へ: カテゴリ <x> の完成品の型が無い
参謀へ: QA が <理由> で毎回落ちる
参謀へ: 同時契約上限を 3 → 4 にしたい（人間が決めた）
```

やること: `cw-engine/**` のコードと文書を直し、`node src/self-test.js` を通し、PR を更新して止まる。
やらないこと: 毎日の応募指示、ログイン確認、本線ファイルの変更、Grok clone の追加、円の発明、#122 の自己マージ。

## 4. ナオミチへの指示（外部サイトと可否だけ）

一度だけ: `docs/HUMAN_ONCE.md`（非公開リポジトリ・Secret・Run workflow）。

毎回の流れ（1 案件）:

1. 公開ページで合う仕事を見つけたら Issue に `CW: JOB <id>`（本文を貼れば確実）
2. `cw-apply:` の応募稿の（人間が書く）を埋めて、クラウドワークスで送る → `CW: SENT <id>`。送らないなら `CW: SKIP <id>`
3. 相手の文が来たら `CW: MSG <id>` + 文 → 返信下書きを貼る
4. **受注するか決める**。契約したら `CW: CONTRACT <id>` + メモ。断るなら `CW: REJECT <id>`
5. 仮払い確認 → 素材を `CW: MAKE <id>` に貼る → Grok が書いて `CW: DRAFT <id>` → `cw-deliver:` の DELIVERY.md を見て納品ボタン → `CW: DELIVERED <id>`
6. 修正依頼は `CW: REVISE <id>` + 依頼文
7. 報酬確定を画面で見た日だけ `CW: PAID <id> <整数円>`

やらないこと: パスワードを Bot に渡す、仮払い前に着手、LINE 等に移る、無い実績を書く、公開の報酬表示を PAID に書く、HQ の Issue に CW を書く。
