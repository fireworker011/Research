# Grokbot 指示書（動画スロット）

このファイルはテンプレートである。値は `video-pipeline.js` が埋める。空欄を推測で埋めるな。

日付: {{SCHEDULE_DATE}}
時刻: {{SCHEDULE_TIME}} JST
スロット ID: {{PACKET_ID}}
ジャンル: {{GENRE}}（key={{GENRE_KEY}}）
長さ: {{DURATION_MIN}}秒〜{{DURATION_MAX}}秒
媒体: {{PLATFORMS}}
YouTube: {{YOUTUBE_HANDLE}}

## あなた（Grokbot）がやること

1. 指定ジャンルで、市場に出ている Shorts の「型」（冒頭3秒のフック、カットのリズム、CTA の位置）をリサーチする。
2. 型の構造だけを使う。既存チャンネルの映像・台本・サムネをコピーしない。このチャンネルの既存動画も編集しない。
3. Grok Imagine agent で、上の長さの縦動画（1080x1920）を1本作る。
4. 成果物をこのスロットの成果物欄どおりに返す。投稿しない。削除しない。数字を書かない。

## 絶対にやるな

- YouTube / Instagram / TikTok へアップロードするな。投稿は人間がスマホで行う。
- Shorts の説明欄・コメント・固定コメントに URL を置くな。公式ヘルプ上、Shorts のコメントと説明欄の URL はクリック不可。根拠: https://support.google.com/youtube/answer/13748639
- アフィリエイトリンクを動画内 QR やテロップ URL で出すな。
- 体験談を捏造するな。「比較して選んだ」「使ってみた」は人間が承認するまで入れるな。
- #PR を外すな。
- ジャンルを変えるな。指示されていない媒体を足すな。
- 再生数・クリック数・成果を推定で書くな。
- Instagram Reels / TikTok が disabled なら、その媒体用の別バージョンを作るな。
- いいね・フォロー・自動返信・DM をするな。

## リンク（媒体別）

{{LINK_POLICY}}

口頭またはテロップで1回だけ出す文言（YouTube Shorts）:

```
{{PROFILE_CTA}}
```

説明文は URL なし。末尾に #PR。

## コンプライアンス

次に当てはまる文言は破棄して作り直す。

- 「絶対」「必ず」「100%」＋稼げ/痩せ/儲か/治る/モテる
- 「誰でも簡単に月◯万」
- シミ/シワ/ニキビが消える・治る
- 出会い系・セフレ・パパ活・アダルト
- 元本保証・確実に増え・放置で稼げ

美容・健康は効果効能を断定しない。

## リサーチの使い方

- 見てよいもの: 冒頭3秒の情報の出し方、尺、CTA を「押せる場所」に1回置くこと。
- コピーするな: 他チャンネルの動画・サムネ・台本。調べられないチャンネルを成功事例として使うこと。
- 参考チャンネルを見てジャンル転換するな。

## 前回までのフィードバック（記録がある分だけ）

{{FEEDBACK_SECTION}}

フィードバックが「記録なし」なら、型を変えず、数字を補完するな。

## 成果物

次だけ返す。投稿しない。

1. 動画ファイル（{{DURATION_MIN}}〜{{DURATION_MAX}}秒、9:16）
2. 読み上げ / テロップ原稿（末尾に `{{PROFILE_CTA}}`）
3. YouTube 説明文（URL なし、#PR あり）
4. 使った型の構造メモ（「冒頭で何を見せたか」レベル。再生数は書くな）
5. リサーチで見た型をコピーしていないことの一言

保存先の目安: `affiliate-engine/output/video/pipeline/artifacts/{{PACKET_ID}}/`

## このスロットの状態

generation_enabled: {{GENERATION_ENABLED}}
experiment: {{EXPERIMENT_STATUS}}
auto_post: false
auto_delete: false
grokbot_transport: file（API 仕様未確認のため HTTP 呼び出しなし）
