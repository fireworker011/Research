# 今やること（CW）

人間が残すのは **案件の契約・外部サイトの案内誘導・納品** だけ。ほかは Grok Bot「CW受注」と司令塔。Cursor を起こさない。HQ clone に足さない。Anthropic 不要。新しい Bot は作らない。

## 済

- `cw-work`、`cw.yml`、Issue `CW — 司令塔`、自己PR
- Bot ID `6416ebcd-6cd0-42bb-92c3-55e00b13828c`

## 今（未了）

1. **CW受注** の「指示」をこれに差し替える  
   https://github.com/fireworker011/Research/blob/cursor/cw-auto-commander-c1fb/cw-engine/docs/grok-bots/G_cw.txt
2. ルーチン **CW採用連絡チェック** をこれに差し替える  
   https://github.com/fireworker011/Research/blob/cursor/cw-auto-commander-c1fb/cw-engine/docs/grok-bots/G_cw_watch.txt
3. 契約待ち・納品待ちだけ人間が押す。案内・誘導が要るときも人間

## 役割

| 誰 | やる |
|---|---|
| **人間** | 契約する／断る。外部サイトへの案内・誘導。納品ボタン。画面で見た確定円 `CW: PAID` |
| **Grok** | 仕事を探す、`CW: JOB`、応募して `SENT`、メッセージ、素材、完成品 `DRAFT` |
| **司令塔** | 資格判定、応募稿、定型返信、QA、台帳。応募 POST はしない |

## やらなくていい

- 新しい Bot、HQ への報告、応募連発（下書き 3 で止まれ）、無い実績、仮払い前着手、LINE へ移す、conversions.csv に CW
