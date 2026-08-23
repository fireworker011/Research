# サクラIG

ゴールはフォロワー増ではない。リールが届き、リンクタップが週15を超え、Fanvueの課金が判定できること。

時計: `schedule.md`

## 仕組み（直接投げられないので Issue 経由）

```
05:00  マネージャーが CURRENT.json を書く
       → GitHub Action が Issue「サクラ起動キー」にコメント
05:00〜06:00  サクラ専属自動投稿がそのコメントを読む
       → IMAGINE_THROW を Grok Imagine agent へ
06:00  Action が「投稿せよ」と Issue に書く
       → ボットが投稿（テストは post:false で投稿しない）
```

ボットの起動文はこれだけ。

`Issue「サクラ起動キー」の最新コメントを読め。IMAGINE_THROW を Imagine に投げろ。文を足すな。`

**`XAI_API_KEY` は不要。** 生成は Grok bot が Grok Imagine agent に投げるだけ。xAI HTTP API は使わない。

## 毎日（JST）

| 時刻 | 誰 | 仕事 |
|---|---|---|
| **05:00** | マネージャー | 起動キーを書いて渡す（Imagine には投げない） |
| 05:00〜06:00 | サクラ専属自動投稿 | 動画作成 |
| **06:00** | サクラ専属自動投稿 | 投稿 |

## 起動キー

`launch-keys/CURRENT.md` / `CURRENT.json`
