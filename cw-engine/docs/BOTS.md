# Bot 役への指示（全部。ここが正）

CW 全自動受注は **5 役**。増やさない。各役の指示は下の枠をそのまま使う。

| 役 | 実体 | 常時？ | 触ってよい場所 |
|---|---|---|---|
| 0. 総統括 | Cursor「１００万円売り上げ自動化」 | 起こされた日だけ | 本線。CW は側線として可否だけ |
| 1. CW 司令塔（機械） | 非公開リポジトリの GitHub Actions（`private-repo/cw.yml`）が `cw-engine/src/apply-commander-comment.js` を回す | イベント駆動（人間のコメント） | 非公開リポジトリの Issue `CW — 司令塔` と同リポジトリのファイル |
| 2. CW 前面（既存1） | Grok Bot「CW受注」`6416ebcd-6cd0-42bb-92c3-55e00b13828c` | 人間が開いたとき＋平日ルーチン | 応募・下書き・完成品。契約・外部誘導・納品はしない |
| 3. CW 総責任者 | Cursor（この PR の作者） | `参謀へ:` で起こされた日だけ | `cw-engine/**` と CI。本線は触らない |
| 4. ナオミチ | 人間 | 契約・外部サイトの案内誘導・納品 | クラウドワークスのその3つと `CW: PAID` |

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

やらない: エンジンへの応募 POST、`RESUME`、円の発明、素材に無い事実、公開リポジトリへの書き込み、HQ Issue への書き込み。
`ANTHROPIC_API_KEY` は不要。応募と完成品は Grok。契約・外部案内誘導・納品は人間。QA は機械。

## 2. CW 前面（Grok・既存1）への指示

貼る先は **新しい会話ではない**。既存 Bot `6416ebcd-6cd0-42bb-92c3-55e00b13828c` の「指示」に [`G_cw.txt`](grok-bots/G_cw.txt)。ルーチン「CW採用連絡チェック」には [`G_cw_watch.txt`](grok-bots/G_cw_watch.txt)。名簿は [`ROSTER.md`](grok-bots/ROSTER.md)。**HQ clone とは別。** 要点:

```
人間は契約・外部案内誘導・納品だけ。ほかは全部やれ。
公開の文章系を JOB → 応募して SENT。相手文は MSG。完成品は DRAFT。
契約ボタン・納品ボタン・LINE等への誘導はするな。PAID を代筆するな。HQ へ帰すな。remain / n10 を開けるな。
```

旧「司令部が指定した案件に応募する」は捨て、上の `G_cw.txt` に差し替える。HQ clone にこの dump を足すな。

## 3. CW 総責任者（Cursor）への指示

起きる条件は `参謀へ:` の1行だけ。例:

```
参謀へ: カテゴリ <x> の完成品の型が無い
参謀へ: QA が <理由> で毎回落ちる
参謀へ: 同時契約上限を 3 → 4 にしたい（人間が決めた）
```

やること: `cw-engine/**` のコードと文書を直し、`node src/self-test.js` を通し、PR を更新して止まる。
やらないこと: 毎日の応募指示、ログイン確認、本線ファイルの変更、Grok clone の追加、円の発明、#122 の自己マージ。

## 4. ナオミチへの指示（3 つだけ）

一度だけ: `docs/HUMAN_ONCE.md` の指示差し替え。

毎回（人間）:

1. **契約** — 受けるなら `CW: CONTRACT <id>`。断るなら `CW: REJECT <id>`
2. **外部サイトの案内・誘導** — LINE 等へ移さない。案内が要るときだけ人間が書く
3. **納品** — DELIVERY.md を見て納品ボタン → `CW: DELIVERED <id>`。確定を画面で見たら `CW: PAID <id> <整数円>`

ほか（探す・応募・返信・完成品）は Grok。パスワードを Bot に渡すな。仮払い前に着手するな。HQ の Issue に CW を書くな。
