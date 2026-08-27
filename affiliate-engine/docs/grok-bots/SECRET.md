# Secret の入れ方（参謀・URL を Git に書くな）

指令塔が `YouTubeあり` と返したあとの仕事。`YouTubeなし` / `項目なし` では使わない。cron は戻さない。転職 YouTube は始めない（台帳 `make: never`）。

## 入れるもの

GitHub Secret 名: `AFFILIATE_LINKS_JSON`  
中身: JSON オブジェクト。鍵は **`転職_neo` だけ**。値は A8 管理画面で発行した広告リンク（チャットに貼るな）。

`config/links.json` の値は空文字のまま。

例の形（URL はダミー。本番の値をここに書くな）:

```
{"転職_neo":"https://example.invalid/replace-in-github-secret-only"}
```

他の鍵（`申込_auひかり` / `教育_N高` / `ペット_Furbo`）は、指令塔が別途「入れてよい」と出すまで足すな。

次の仕事（結合するな）: `dump/G_hq_threads_profile.txt`。Secret だけではクリックできない。

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
