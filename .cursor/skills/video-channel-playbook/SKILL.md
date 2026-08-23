---
name: video-channel-playbook
description: A8案件別動画チャンネルの作業手順。ベンチマーク分析、Grok/Cursor制作、15分×4の日次ルーティン。量産や多媒体の提案の前に読む。
---

# 動画チャンネル運用（手順書）

本体は `affiliate-engine/docs/video-channel-playbook.md`。  
判断基準は `video-cash-loop` スキルと `affiliate-engine/docs/video-cash-loop.md` が上位。矛盾したらキャッシュループ側に従う。

## このスキルで出すもの

ユーザーが次のいずれかを頼んだとき、プレイブックの該当節を開いて **コピー用テキストだけ** 出す。

- ベンチマーク分析の項目・手順 → §1
- Grok Imagine / Cursor の制作プロンプト → §2
- 日々の作業ルーティン（15分×4） → §3
- Grok Bot に作る9体 → `affiliate-engine/docs/grok-bots/CREATE.md`。各体は「これだけ読んで」でそのジャンルの動画を生成する。投稿はしない

## 先に固定する役割

- Cursor: 記録、台本枠、プロンプト、`video-semi-auto.js` の説明。投稿しない
- Grok Imagine: 文字なしの縦型素材。投稿ボットにしない
- 人間: 公式アプリで投稿、A8とスタジオの数字、体験文言の承認

## やってはいけないこと

- YouTube / TikTok / Instagram を同時に「今日やること」として出す
- 全A8案件のチャンネル開設を今日のタスクにする（駐車場は §5。ゲート後に1つ）
- 参考チャンネルの動画・台本・サムネをコピーする
- 実験中（`TODAY.md` が `CONTINUE_EXPERIMENT`）に新しい台本を創る
- Shorts の説明欄・コメントにURLを置く
- 数字が無い行を埋める
- `insight.js` を動画に使う

## 定期実行との切り分け

エージェントが「起きただけ」なら `video-cash-loop` の定期実行に従う。  
このスキルは、人間が分析・制作・ルーティンを頼んだときにだけ使う。
