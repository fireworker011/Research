# Secret の入れ方（参謀・URL を Git に書くな）

指令塔が `YouTubeあり` と返し、副サイト登録（`SITE.md`）のあとの仕事。`YouTubeなし` / `項目なし` では使わない。cron は戻さない。転職 YouTube は始めない（台帳 `make: never`）。

値は A8 管理画面で、**掲載サイトに登録した転職 Threads を選んで**発行した広告リンク（チャットに貼るな）。未登録のまま発行するな。

## 入れるもの

GitHub Secret 名: `AFFILIATE_LINKS_JSON`  
中身: JSON オブジェクト。鍵は **`転職_neo` だけ**。値は上の発行リンク。

`config/links.json` の値は空文字のまま。

例の形（URL はダミー。本番の値をここに書くな）:

```
{"転職_neo":"https://example.invalid/replace-in-github-secret-only"}
```

他の鍵（`申込_auひかり` / `教育_N高` / `ペット_Furbo`）は、指令塔が別途「入れてよい」と出すまで足すな。

次の仕事（結合するな）: `dump/G_hq_threads_profile.txt`。Secret だけではクリックできない。

## 本番ジョブは sprint を読まない

post / insight / report は `claude/monthly-revenue-system-gvi02u` を checkout する。実測: `docs/grok-bots/CHECKOUT.md`。

Secret を入れても、そのブランチに `loadLinks()` が無いあいだは自動投稿は空キーのまま。今夜のクリック場所はプロフィールリンク欄（手動）。自動投稿の再開は指令塔が出すまでしない。

## 貼る位置（指令塔が「貼ってよい」と出したあと）

| 媒体 | 位置 | やるな |
|---|---|---|
| Threads | プロフィールのリンク欄 | スレッド本文の広告リンク。cron 再開 |
| YouTube | 指令塔が指定した既存動画の詳細欄 + `#PR` + 有料プロモーション | 新規チャンネル。動画内URL。ShortsコメントのアフィURL。転職ジャンルの量産 |

## やらないこと

- URL を Git / チャット / Issue / dump に書く
- `links.json` に値をコミットする
- post / insight の schedule を戻す
- 項目なしの auひかりを入れる
- カタログ 15000 円を conversions に足す
