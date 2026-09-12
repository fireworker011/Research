# HQ 統括命令（Cursor だけ。Grok Bot は開けるな）

発令: 2026-09-12。目標は変えない。9/30 確定 ¥1,000,000。

## 指揮系統

```
ナオミチ（外部サイト・重要判断。席は1回）
  └ 総司令 Cursor
       https://cursor.com/agents/bc-9e6f3a09-eff4-42b2-adbe-9caa1758a971
       名前: １００万円売り上げ自動化
       ├ GitHub 指示役（dump 選択。投稿しない）
       ├ Grok Bot 1 clone（日常。dump 1ファイル）
       └ 他の Cursor = 側線。総司令を名乗らない。デフォルト本線を勝手に触らない
```

総司令が持つもの: 台帳 `HQ_ROSTER.md`、カレンダー `HQ_CALENDAR.md`、dump 選択、本線 PR の可否。
総司令が持たないもの: A8 ログイン、Secret 貼り付け、XM 実発注、他エージェントのダッシュボード Archive（それはナオミチ）。

## 他の Cursor が起動したら（命令）

1. このファイルと `HQ_ROSTER.md` を読め。Grok の dump を結合するな。
2. 自分を「司令塔」「総司令」と名乗るな。新しい clone を本線に足すな。
3. `hq-instruct.js` / `G_hq_boot.txt` / LIVE dump / `MACHINE.md` を側線の都合で上書きするな。
4. デフォルトへ出す PR は、円の席を壊さないものだけ。迷ったら出すな。
5. ログイン確認ループをするな。Threads cron を戻すな。数字を invent するな。
6. 足りない仕組みは人間チャットに `参謀へ:` 1行。新エージェントを増やすな。

## 総司令が許可するデフォルトマージ

| PR | 内容 |
|---|---|
| [#123](https://github.com/fireworker011/Research/pull/123) | この台帳と統括命令 |
| [#113](https://github.com/fireworker011/Research/pull/113) | 空 link_key をジャンルURLへ落とさない（cron は止まったまま） |
| [#88](https://github.com/fireworker011/Research/pull/88) | overlay_status を PR でも回す（投稿しない） |

[#112](https://github.com/fireworker011/Research/pull/112) は席 boot と衝突する。載せるなら総司令が rebase したあと。

## 総司令が禁止するデフォルトマージ

[#122](https://github.com/fireworker011/Research/pull/122) CW レーンを instruct/boot に差す。
[#94](https://github.com/fireworker011/Research/pull/94) XM iPhone。ペーパーは Issue 93 で足りる。
[#75](https://github.com/fireworker011/Research/pull/75) 古い100万ループ。[#104](https://github.com/fireworker011/Research/pull/104) 動画投稿エンジン。
H3 系は h3 ブランチに置け。デフォルトへ向け直すな。FANZA を Threads 9アカに出すな。

## いま動いている Cursor

RUNNING は総司令だけ。ERROR の JPEG アップローダ2体は Archive してよい。IDLE の CW/XM/H3 は起こすな。
