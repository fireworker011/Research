# Commands（非公開リポジトリの Issue「CW — 司令塔」）

1行目に `CW: <コマンド> <仕事ID>`。2行目以降が本文。大文字小文字は問わない。1コメント1コマンド。

| 行 | 誰 | 意味 |
|---|---|---|
| `CW: JOB <id>` + 公開文 | 人間 | 取込 → 資格判定 → 応募稿。本文が無ければ公開ページを1回読む。`category=<id>` `applied=yes` を1行目に足せる |
| `CW: SENT <id>` | 人間 | 応募稿を貼って送った |
| `CW: SKIP <id>` | 人間 | 見送り |
| `CW: MSG <id>` + 相手の文 | 人間 | 定型返信の下書き |
| `CW: CONTRACT <id>` + メモ | 人間 | **受注した**（可否は人間）→ BRIEF |
| `CW: MATERIAL <id>` + 素材 | 人間 | 素材を足す |
| `CW: MAKE <id>` (+素材) | 人間 | Grok 用プロンプト（Anthropic 不要） |
| `CW: DRAFT <id>` + 本文 | Grok / 人間 | 完成品を貼る → QA → 納品パッケージ |
| `CW: REVISE <id>` + 修正依頼 | 人間 | 反映版のプロンプト → また `CW: DRAFT` |
| `CW: DELIVERED <id>` | 人間 | 納品ボタンを押した |
| `CW: PAID <id> <整数円> <メモ>` | 人間 | 画面で確定を見た日だけ。カンマ・カタログ・URL は拒否 |
| `CW: REJECT <id>` | 人間 | 不採用・失注 |
| `CW: PROFILE` | 人間 | 自己PR の下書き |
| `CW: HALT` | 人間 / CW 前面 | 新規の資格判定を止める |
| `CW: PAPER_ONLY` | 人間 | 既定に戻す |
| `CW: DESK` | 誰でも | デスクだけ出す |

`cw-apply:` `cw-reply:` `cw-brief:` `cw-make:` `cw-deliver:` `cw-qa:` `cw-profile:` `cw-note:` `cw-desk:` は機械の告知。指令ではない。

`CW: RESUME` は **無い**。自動送信のライブゲートを作らない。
`CW: GO` / `AFFI: GO` は本線（`Grok Bot — 指示`）の言葉。この Issue には無関係。

カテゴリ id: `writing_article` `writing_sns` `writing_script` `writing_copy` `text_cleanup` `translation` `data_structuring` `video_edit_short`
