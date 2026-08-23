# 毎日の時計（JST）

投稿が 06:00 なので、起動キーは **05:00 までに渡す**。  
別の Grok bot に直接メッセージは送れない。受け渡しは **GitHub Issue「サクラ起動キー」** を使う。

| JST | 誰 | 仕事 |
|---|---|---|
| **05:00** | マネージャー | `launch-keys/CURRENT.md` を書く。`sakura_ig_handoff.yml` が Issue にコメントする |
| 05:00〜06:00 | サクラ専属自動投稿 | Issue の最新コメントの `IMAGINE_THROW` を Imagine に投げる。動画完成 |
| **06:00** | ワークフロー + ボット | `sakura_ig_post_gate.yml` が「投稿せよ」と Issue に書く。ボットが投稿する |

1日1本。05:00 の Issue 更新が無い日は、ボットは動かない。

テストは `post: false`。投稿ゲートも「投稿するな」と書く。

cron はデフォルトブランチへのマージ後に生きる。それまでは `CURRENT.json` を push するか、Actions の手動実行。
