# Secret の入れ方・教育（参謀・URL を Git に書くな）

指令塔が N高またはアイズで `Threadsあり` と返し、副サイト登録（`SITE_EDU.md`）のあとの仕事。`YouTubeあり` / `項目なし` / `媒体なし` / `未開設` では使わない。cron は戻さない。教育 YouTube は始めない（台帳 `make: never`）。
neo 用は `SECRET.md`。チケット用は `SECRET_TICKET.md`。混ぜるな。転職アカに N高／アイズを入れるな。教育アカに neo を入れるな。

値は A8 管理画面で、**掲載サイトに登録した教育 Threads を選んで**発行した広告リンク（チャットに貼るな）。未登録のまま発行するな。

## 入れるもの

GitHub Secret 名: `AFFILIATE_LINKS_JSON`  
中身: JSON オブジェクト。鍵は dump が指名した **1つだけ**（`教育_N高` または `教育_アイズ`）。値は上の発行リンク。

`config/links.json` の値は空文字のまま。

例の形（URL はダミー。本番の値をここに書くな）:

```
{"教育_N高":"https://example.invalid/replace-in-github-secret-only"}
```

アイズ経路なら鍵は `教育_アイズ` だけ。同じ JSON に `転職_neo` を足すな（neo は別 dump）。N高を既に入れたならアイズで上書きするな。

`config/links.json` と Git / チャットに URL を書くな。

次の仕事（結合するな）: N高なら `dump/G_hq_threads_profile_edu.txt`。アイズなら `dump/G_hq_threads_profile_eyes.txt`。Secret だけではクリックできない。

## 本番ジョブは sprint を読まない

post / insight / report は `claude/monthly-revenue-system-gvi02u` を checkout する。実測: `docs/grok-bots/CHECKOUT.md`。今夜のクリック場所は教育プロフィールリンク欄（手動）。自動投稿の再開は指令塔が出すまでしない。

## やらないこと

- `転職_neo` / `申込_auひかり` / `ペット_Furbo` をこの dump で入れる
- 教育 YouTube を始める
- URL を Git / チャット / Issue / このファイルに書く
- post / insight の schedule を戻す
- カタログ円を conversions に足す
