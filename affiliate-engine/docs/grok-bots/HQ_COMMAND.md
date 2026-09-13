# HQ 統括命令（Cursor だけ。Grok Bot は開けるな）

発令: 2026-09-12。目標は変えない。9/30 確定 ¥1,000,000。

## 指揮系統

```
ナオミチ（外部サイト・重要判断。席は1回）
  ├ 総司令 Cursor（ピン留めチャット）
  │    名前: １００万円売り上げ自動化
  │    id: bc-9e6f3a09-eff4-42b2-adbe-9caa1758a971
  │    ├ GitHub 指示役（dump 選択。投稿しない）
  │    ├ Grok 管理者（読んで担当者へ実施。コードしない）
  │    │    id: b6bf30a6-a4f5-41ca-a2db-b417d936b9f4
  │    │    入口: dump/G_hq_admin.txt
  │    │    ├ 日常 Grok 1 clone（dump 1ファイル。G_hq_boot.txt）
  │    │    ├ 人間（ナオミチ）の席1回
  │    │    ├ X @comback_nao6（過程。確定円0を成果と書くな）
  │    │    └ XM（AFFI: STOP のときだけ）
  │    └ 他のピン留め Cursor = 側線。総司令を名乗らない。デフォルト本線を勝手に触らない
  └ 独立（指揮外。命令しない。管理者も振るな）
       ├ 専用ストーリー再生  bc-01a07bb1-da1a-7a05-a8a2-2c4a85bcf112
       └ bc-bca5f77f-03dd-4bd9-b290-84557e23ab58
```

総司令が持つもの: 台帳 `HQ_ROSTER.md`、カレンダー `HQ_CALENDAR.md`、dump 選択、本線 PR の可否。ピン留めチャットの統括。Grok 管理者への命令（読むファイルと今日の実施1つ）。
総司令が持たないもの: A8 ログイン、Secret 貼り付け、XM 実発注、他エージェントのダッシュボード Archive（それはナオミチ）。独立2体への作業指示。担当者への直接采配（それは Grok 管理者）。

## Grok 管理者（Cursor が命令する）

Automation API からは見つからない。ナオミチ指定どおり管理者。このチャットだけが管理者。他の Grok は担当者。

1. 管理者に `dump/G_hq_admin.txt` を一度読ませろ。毎日貼り直すな。HQ_COMMAND / HQ_ROSTER / HQ_CALENDAR は開けるな。
2. 次に Issue `Grok Bot — 指示` の最新 `hq-instruct:` が指す **1ファイル**だけ読ませろ。
3. 読んだあと、担当者へ実施を **1つ**出させろ。自分で席・投稿・コードをさせるな。独立2体に振るな。
4. 席の印 `完了` のあと overlay が空なら、今日の実施は Secret。席のやり直しを出すな。X は過程だけ。確定円0を成果と書くな。

## 独立（指揮外）

ナオミチが除外した2体。総司令は仕事を振らない。管理者も振るな。H3 ブランチの PR を閉じない。100万の LIVE dump / `hq-instruct.js` / `G_hq_boot.txt` / `G_hq_admin.txt` は触るな。

| 体 | 実体 | 扱い |
|---|---|---|
| 専用ストーリー再生 | `bc-01a07bb1-da1a-7a05-a8a2-2c4a85bcf112`。ブランチ `cursor/h3-real-shaft-f112`。PR #118 ほか H3 側線 | H3 ベースで独立。デフォルトへ向け直すな |
| （名称未検出） | `bc-bca5f77f-03dd-4bd9-b290-84557e23ab58` | この環境の Cloud Agent 一覧には無い。ピン留め指定どおり独立 |

## 他の Cursor が起動したら（命令）

あなたが上の独立2体なら、この節は無視してよい。100万の LIVE dump と `hq-instruct.js` は触るな。

1. このファイルと `HQ_ROSTER.md` を読め。Grok の dump を結合するな。
2. 自分を「司令塔」「総司令」と名乗るな。新しい clone を本線に足すな。
3. `hq-instruct.js` / `G_hq_boot.txt` / `G_hq_admin.txt` / LIVE dump / `MACHINE.md` を側線の都合で上書きするな。
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
FANZA を Threads 9アカに出すな。独立2体の H3 PR をデフォルトへ向け直すな（H3 ベースは彼らの管轄）。

## いま動いている Cursor

RUNNING は総司令だけ。ERROR の JPEG アップローダ2体は Archive してよい。IDLE の CW/XM は起こすな。独立2体は起こしてよい（指揮しない）。
