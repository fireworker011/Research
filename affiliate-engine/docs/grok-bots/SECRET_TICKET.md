# Secret の入れ方・チケット（参謀・URL を Git に書くな）

指令塔がチケットで `Threadsあり` と返し、副サイト登録（`SITE.md`）のあとの仕事。`YouTubeあり` / `項目なし` / `媒体なし` / `未開設` では使わない。cron は戻さない。転職 YouTube は始めない（台帳 `make: never`）。
neo 用は `SECRET.md`。教育用は `SECRET_EDU.md`。混ぜるな。neo を既に Secret に入れた／プロフィールに置いたならこのファイルは使うな（同じ欄を上書きするな。次はバナー）。

値は A8 管理画面で、**掲載サイトに登録した転職 Threads を選んで**発行した広告リンク（チャットに貼るな）。未登録のまま発行するな。

## 入れるもの

GitHub Secret 名: `AFFILIATE_LINKS_JSON`  
中身: JSON オブジェクト。鍵は **`転職_チケット` だけ**。値は上の発行リンク。

`config/links.json` の値は空文字のまま。

例の形（URL はダミー。本番の値をここに書くな）:

```
{"転職_チケット":"https://example.invalid/replace-in-github-secret-only"}
```

同じ JSON に `転職_neo` を足すな（neo は別 dump）。教育アカにチケットを入れるな。

次の仕事（結合するな）: `dump/G_hq_threads_profile_ticket.txt`。Secret だけではクリックできない。

## 本番ジョブは sprint を読まない

post / insight / report は `claude/monthly-revenue-system-gvi02u` を checkout する。実測: `docs/grok-bots/CHECKOUT.md`。今夜のクリック場所は転職プロフィールリンク欄（手動）。自動投稿の再開は指令塔が出すまでしない。

## やらないこと

- neo が入っている Secret / プロフィール欄をチケットで上書きする
- 転職 YouTube を始める
- URL を Git / チャット / Issue / このファイルに書く
- post / insight の schedule を戻す
- カタログ円を conversions に足す
