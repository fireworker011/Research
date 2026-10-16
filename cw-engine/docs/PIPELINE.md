# パイプライン（状態・成果物・誰が押すか）

```
公開ページ ──Grok: CW: JOB──▶ 取込 ─▶ 資格判定 ─┬─ NG ─▶ rejected
                                              └─ OK ─▶ 応募稿 ─▶ drafted
Grok: CWで応募 ─▶ CW: SENT ─▶ sent ──相手の文── Grok: MSG ─▶ 定型返信（CW内）
人間: 契約 ─▶ CW: CONTRACT ─▶ contracted ─▶ BRIEF
Grok: MAKE → DRAFT ─▶ QA ─┬─ fail ─▶ qa_failed
                          └─ pass ─▶ ready
人間: 納品ボタン ─▶ CW: DELIVERED ─▶ delivered ──修正── Grok: REVISE
人間: 画面で確定 ─▶ CW: PAID <円>
```

## 状態

| 状態 | 意味 | 次に押すのは |
|---|---|---|
| rejected | 資格判定で落ちた | Grok: 別の仕事 |
| qualified / drafted | 応募稿あり | Grok: 応募 `SENT` / 見送り `SKIP` |
| sent | 返事待ち | Grok: `MSG`。**人間: `CONTRACT` / `REJECT`**。外部誘導は人間 |
| contracted | BRIEF あり | Grok: 素材 `MAKE`（仮払い後） |
| making | プロンプト待ち | Grok: `DRAFT` |
| making → qa_failed | QA 不合格 | Grok: `DRAFT` |
| making → ready | DELIVERY.md あり | **人間: 納品ボタン → `DELIVERED`** |
| delivered | 検収待ち | Grok: `REVISE`。人間: `PAID` |
| paid | 台帳に確定 | 終わり |
| skipped / lost | 見送り・失注 | 終わり |

## 成果物の置き場（非公開リポジトリ）

```
work/
  state/commander.json  state/queue.json
  data/cw_ledger.csv
  jobs/<id>/JOB.md  APPLY.md  BRIEF.md
  jobs/<id>/messages/NN_in.md  NN_reply.md
  jobs/<id>/materials/NN.md
  jobs/<id>/GROK_PROMPT.md
  jobs/<id>/deliverables/vN/deliverable.md|.csv  deliverable.txt  QA.md  DELIVERY.md
  profile/PROFILE.md
  reports/TODAY.md
```

## 資格判定（LLM に選ばせない）

落とす: 募集終了 / 既応募 / 顔出し・出演・撮影 / AI 使用禁止 / 口コミ・レビュー投稿（規約22条21） / 被リンク・順位操作（20） / ランキング操作（22） / アフィ・会員登録代行（24） / アカウント作成・貸与（23） / MLM（18） / レポート・論文代行 / アダルト / 個人情報の入力・収集 / 実績必須なのに納品 0 / カテゴリ不明 / 素材なしの動画編集 / HALT 中 / 同時契約が上限。
注意（落とさない）: 外部連絡の誘導 / 仮払い前作業の匂い / AI 申告必須 / スクール除外 / 応募が募集の10倍。
優先度: カテゴリ優先度 + 未経験可 + 継続 + 枠余り + 応募項目が少ない − AI完結でない。

## 完成品の型（`make.js` のプロンプト。本文は Grok）

| カテゴリ | 出力 | 備考 |
|---|---|---|
| writing_article | Markdown 記事（見出し付き）+ .txt | 事実は素材だけ。無いものは【要確認】 |
| writing_sns | 投稿文（`---` 区切り） | ハッシュタグは素材か指示にあるものだけ |
| writing_script | 台本（ナレーション: / テロップ:） | 秒数は指示があるときだけ |
| writing_copy | 商品説明・コピー | 効果断定・最上級は使わない |
| text_cleanup | 整文・要約 | 内容を足さない |
| translation | 訳文 + 最小の【訳注】 | 原文に無い情報を足さない |
| data_structuring | CSV（ヘッダ行あり） | 無い値は空欄 |
| video_edit_short | 編集計画（カット表・テロップ原稿） | 動画そのものは人間のツール。主力ではない |

QA で落ちる: 【要確認】が残る / 素材に無い URL・電話・メール / 治る・必ず・No.1 などの断定 / メタAI発言 / コードフェンス / 分量の逸脱。
