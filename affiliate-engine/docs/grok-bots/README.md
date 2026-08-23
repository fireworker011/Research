# Grok bot 起動キー一式

各ファイルの本文を、そのボットの **最初のメッセージ（またはカスタム指示）にそのまま貼る。**  
文を足すな。同時に起動してよいのは **LIVE** だけ。

受け渡しはファイル。Grok bot 同士は直接メンションできない（サクラと同じ）。  
投稿・いいね・フォロー・固定コメントは、どのキーでも禁止。人間が公式アプリでやる。

サクラ系統はここには置かない。Issue [#54 サクラ起動キー](https://github.com/fireworker011/Research/issues/54) と `sakura-ig/launch-keys/` を使え。

## 今日貼ってよい（LIVE）

| ボット | 起動キー | 仕事 |
|---|---|---|
| 動画Imagine | [LIVE-video-imagine.md](launch-keys/LIVE-video-imagine.md) | 文字なし 9:16 素材。台本は書かない |
| 動画Shorts | [LIVE-video-shorts.md](launch-keys/LIVE-video-shorts.md) | `youtube-next-3.md` の再掲。新作を創らない |
| 動画記録 | [LIVE-video-record.md](launch-keys/LIVE-video-record.md) | CSV 1行の書き方と判定の再掲 |
| 動画ベンチマーク | [LIVE-video-benchmark.md](launch-keys/LIVE-video-benchmark.md) | 確認できるアカウント1件のシート |

## 保存だけ（PARKED）。今日は起動するな

週50クリックが3週、または人間が「このジャンルを出せ」と書いたあと、**1つだけ** `run: parked` を外す。

| ボット | 起動キー | ジャンル |
|---|---|---|
| ジャンル_婚活 | [PARKED-genre-konkatsu.md](launch-keys/PARKED-genre-konkatsu.md) | 婚活 |
| ジャンル_副業 | [PARKED-genre-sidejob.md](launch-keys/PARKED-genre-sidejob.md) | 副業 |
| ジャンル_美容 | [PARKED-genre-beauty.md](launch-keys/PARKED-genre-beauty.md) | 美容 |
| ジャンル_筋トレ | [PARKED-genre-bodymake.md](launch-keys/PARKED-genre-bodymake.md) | 筋トレ |
| ジャンル_教育 | [PARKED-genre-education.md](launch-keys/PARKED-genre-education.md) | 教育 |
| ジャンル_節約 | [PARKED-genre-setsuyaku.md](launch-keys/PARKED-genre-setsuyaku.md) | 節約 |
| ジャンル_転職 | [PARKED-genre-tenshoku.md](launch-keys/PARKED-genre-tenshoku.md) | 転職 |
| ジャンル_ペット拡張 | [PARKED-genre-pet.md](launch-keys/PARKED-genre-pet.md) | ペット（実験の型以外） |
| ジャンル_睡眠 | [PARKED-genre-sleep.md](launch-keys/PARKED-genre-sleep.md) | 睡眠 |

TikTok / Instagram 専用ボットは作らない。媒体追加は人間が1つ承認してから、上のどれか1つに「媒体=…」を足す。

## この束に入れない

- サクラ専属自動投稿 / サクラ Imagine（Issue #54）
- 同人ゲーム工場 / アダアフィ（別系統）
- `video-judge.js`（GitHub Actions。Grok に判定させない）

共通契約: [COMMON.md](COMMON.md)  
日次の使い方: `docs/video-channel-playbook.md` §3
