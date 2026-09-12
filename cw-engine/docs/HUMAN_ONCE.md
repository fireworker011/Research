# 今やること（CW）

日常は Issue `CW — 司令塔` にコメントするだけ。Cursor を起こさない。Grok の HQ clone に CW を足さない。Anthropic API は不要。新しい Grok Bot は作らない。

## 済

- 非公開リポジトリ `fireworker011/cw-work`、`cw.yml`、Actions 成功、Issue `CW — 司令塔`
- クラウドワークスの自己PR更新
- 完成品は Grok（`CW: DRAFT`）。応募送信・契約・納品ボタンは人間
- 使う Bot は既存「CW受注」`6416ebcd-6cd0-42bb-92c3-55e00b13828c` だけ

## 今（未了・この順）

1. **CW受注** の「指示」をこれに差し替える（古い「司令部が指定した案件に応募する」は捨てる）  
   https://github.com/fireworker011/Research/blob/cursor/cw-auto-commander-c1fb/cw-engine/docs/grok-bots/G_cw.txt
2. ルーチン **CW採用連絡チェック** の「指示」をこれに差し替える（見るだけ。HQ へ帰さない）  
   https://github.com/fireworker011/Research/blob/cursor/cw-auto-commander-c1fb/cw-engine/docs/grok-bots/G_cw_watch.txt
3. 実測で残っている契約・採用を司令塔へ一度移す（固定URL監視はやめる）
   - 仮払い完了なら仕事IDと `CW: CONTRACT <id>` + メモ
   - 採用連絡の本文があれば `CW: MSG <id>` + 全文
   - 素材が来ていれば `CW: MAKE <id>` → Grok が書いて `CW: DRAFT`

それが終わったら、新規は合う仕事を1件だけ `CW: JOB <id>` + 公開文。

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

- 新しい Grok Bot、HQ（月100万稼ぐまで帰れま10）への報告、`ANTHROPIC_API_KEY`
- Cursor を24時間動かす。ログイン確認ループ
- 公開リポジトリ `Research` の Issue に CW を書く。`Grok Bot — 指示` にも書かない
- 応募連発。下書き 3 件で新しい JOB は入れない
- 公開の報酬表示を PAID に書く。conversions.csv に CW を足す
- 仮払い前の着手、LINE 等への移行、無い実績
