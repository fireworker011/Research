# Commands（非公開リポジトリの Issue「CW — 司令塔」）

1行目に `CW: <コマンド> <仕事ID>`。2行目以降が本文。大文字小文字は問わない。1コメント1コマンド。

| 行 | 誰 | 意味 |
|---|---|---|
| `CW: JOB <id>` + 公開文 | Grok | 取込 → 資格判定 → 応募稿 |
| `CW: SENT <id>` | Grok | 応募した |
| `CW: SKIP <id>` | Grok | 見送り |
| `CW: MSG <id>` + 相手の文 | Grok | 定型返信の下書き |
| `CW: CONTRACT <id>` + メモ | **人間** | **受注した** → BRIEF |
| `CW: MATERIAL <id>` + 素材 | Grok | 素材を足す |
| `CW: MAKE <id>` (+素材) | Grok | 完成品プロンプト |
| `CW: DRAFT <id>` + 本文 | Grok | 完成品 → QA |
| `CW: REVISE <id>` + 修正依頼 | Grok | 反映版プロンプト |
| `CW: DELIVERED <id>` | **人間** | 納品ボタンを押した |
| `CW: PAID <id> <整数円> <メモ>` | 人間 | 画面で確定を見た日だけ |
| `CW: REJECT <id>` | **人間** | 不採用・失注 |
| `CW: PROFILE` | 人間 | 自己PR の下書き |
| `CW: HALT` | 人間 / CW 前面 | 新規の資格判定を止める |
| `CW: PAPER_ONLY` | 人間 | 既定に戻す |
| `CW: DESK` | 誰でも | デスクだけ出す |

`cw-apply:` `cw-reply:` `cw-brief:` `cw-make:` `cw-deliver:` `cw-qa:` `cw-profile:` `cw-note:` `cw-desk:` は機械の告知。指令ではない。

`CW: RESUME` は **無い**。自動送信のライブゲートを作らない。
`CW: GO` / `AFFI: GO` は本線（`Grok Bot — 指示`）の言葉。この Issue には無関係。

カテゴリ id: `writing_article` `writing_sns` `writing_script` `writing_copy` `text_cleanup` `translation` `data_structuring` `video_edit_short`
