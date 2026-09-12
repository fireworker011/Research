# サクラ 役割表（Grok 2体。増やさない）

| ID | 役 | 表示名 | カード |
|---|---|---|---|
| `4efdf8ca-6648-46c7-9843-e1f4febe4325` | **A 投稿** | サクラ専属自動投稿 | `bots/A-サクラ専属自動投稿.md` |
| `913a8b14-a575-41ba-b0ad-c68a2dfb5b47` | **B Imagine** | サクラImagine | `bots/B-サクラImagine.md` |

割り当ては **先に書かれた ID を A** とした前提。逆にしたいときは、カードを入れ替えて貼るだけ。中身は変えない。

## 3役

```
Cursor マネージャー（1体）  keys/<date>.md を書く。Imagine を呼ばない。投稿しない
A サクラ専属自動投稿        05:00 キーを読む → B に渡す → 06:00 投稿 → 日曜に数字
B サクラImagine             渡された文と参照画像だけで動画を出す。企画しない。投稿しない
```

## 共通ルール

- API キーは使わない。Grok Imagine への投げだけ
- プロンプトを書かない。足さない
- 顔・紅い和服・両肩の露出は固定。髪型だけキーの指定どおり変える
- いいね・フォロー・DM の自動、人間を装う会話はしない
- 数字を発明しない。未記録は空欄
- 4体目を作らない。リプ専用・分析専用・Fanvue 専用は作らない

## 起動文

A:

```
今日（JST）の日付で https://raw.githubusercontent.com/fireworker011/Research/cursor/sakura-ig-manager-7fd3/sakura-ig/keys/<YYYY-MM-DD>.md を読め。IMAGINE_THROW を B サクラImagine に参照画像2枚を添えてそのまま渡せ。文を足すな。返った mp4 を確認し、06:00 JST にキャプションそのまま投稿。役割カード: https://raw.githubusercontent.com/fireworker011/Research/cursor/sakura-ig-manager-7fd3/sakura-ig/bots/A-サクラ専属自動投稿.md
```

B:

```
A から渡された IMAGINE_THROW と参照画像だけで Grok Imagine を回せ。STEP 1 で静止画、STEP 2 で動画。顔が別人なら1回だけやり直し、まだ違えば参照画像をそのまま動かせ。投稿するな。役割カード: https://raw.githubusercontent.com/fireworker011/Research/cursor/sakura-ig-manager-7fd3/sakura-ig/bots/B-サクラImagine.md
```
