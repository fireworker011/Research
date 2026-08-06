# 動画ブリーフ: 2026-08-cleansing-b

- 商品: **△△クレンジングバーム**（クレンジング）
- 悩み: メイク崩れ / 訴求: 体温で溶けるのが早い
- 型: **無音テクスチャASMR型**（`p1_texture_asmr` / Sランク）
- 尺: 12秒 / 必要画像: 5枚 / 配信先: tiktok
- link_key: `skincare_cleansing_b`

> なぜこの型か: 言語に依存しないので量産が最も速く、失敗コストが低い。テクスチャ接写＋ASMRは2026年の定番で、冒頭2秒の視覚フックだけで滞在が伸びる。AI美女は『使ってる人』としてカット3以降に置くだけで成立する。

---

## ① ChatGPT 画像生成プロンプト

先に `prompts/character-sheet.md` でベース画像を1枚作り、**そのベース画像を毎回添付した上で**以下を投げる。
テキストだけで同一人物を出そうとすると必ず顔が変わる。

### カット1（0.0-1.8 視覚フック）
```
同一人物・同一世界観で通すこと。人物設定: 26-29歳に見える、黒髪セミロング、やや目尻の下がった一重寄りの二重、ナチュラルメイク、日本人、清潔感、生活感のある部屋。衣装: オフホワイトのリブトップス／グレーのルームウェア。場所: 自然光の入る洗面台、白いタイル、木のトレー。写真的リアリズム、自然光、9:16縦構図、被写界深度浅め、加工しすぎない肌質（毛穴とうぶ毛を残す）。禁止: 露出の高い服装、扇情的なポーズ、実在の芸能人に似せる、ブランドロゴの改変。
【カット1（視覚フック）】手の甲／指先でのテクスチャ超接写。とろみが糸を引く、粒が溶ける。この画像は静止画として完結させ、次の工程で動かす前提のため、被写体の輪郭がフレーム端で切れないようにする。
```

### カット2（1.8-4.0 文脈提示）
```
同一人物・同一世界観で通すこと。人物設定: 26-29歳に見える、黒髪セミロング、やや目尻の下がった一重寄りの二重、ナチュラルメイク、日本人、清潔感、生活感のある部屋。衣装: オフホワイトのリブトップス／グレーのルームウェア。場所: 自然光の入る洗面台、白いタイル、木のトレー。写真的リアリズム、自然光、9:16縦構図、被写界深度浅め、加工しすぎない肌質（毛穴とうぶ毛を残す）。禁止: 露出の高い服装、扇情的なポーズ、実在の芸能人に似せる、ブランドロゴの改変。
【カット2（文脈提示）】ボトルを持つ手元。ラベルは3カット目までは寄りすぎない。この画像は静止画として完結させ、次の工程で動かす前提のため、被写体の輪郭がフレーム端で切れないようにする。
```

### カット3（4.0-7.5 人物投入）
```
同一人物・同一世界観で通すこと。人物設定: 26-29歳に見える、黒髪セミロング、やや目尻の下がった一重寄りの二重、ナチュラルメイク、日本人、清潔感、生活感のある部屋。衣装: オフホワイトのリブトップス／グレーのルームウェア。場所: 自然光の入る洗面台、白いタイル、木のトレー。写真的リアリズム、自然光、9:16縦構図、被写界深度浅め、加工しすぎない肌質（毛穴とうぶ毛を残す）。禁止: 露出の高い服装、扇情的なポーズ、実在の芸能人に似せる、ブランドロゴの改変。
【カット3（人物投入）】AI美女：洗面台の鏡ごし、頬に伸ばす手元中心（顔は3割）。この画像は静止画として完結させ、次の工程で動かす前提のため、被写体の輪郭がフレーム端で切れないようにする。
```

### カット4（7.5-10.0 質感の再フック）
```
同一人物・同一世界観で通すこと。人物設定: 26-29歳に見える、黒髪セミロング、やや目尻の下がった一重寄りの二重、ナチュラルメイク、日本人、清潔感、生活感のある部屋。衣装: オフホワイトのリブトップス／グレーのルームウェア。場所: 自然光の入る洗面台、白いタイル、木のトレー。写真的リアリズム、自然光、9:16縦構図、被写界深度浅め、加工しすぎない肌質（毛穴とうぶ毛を残す）。禁止: 露出の高い服装、扇情的なポーズ、実在の芸能人に似せる、ブランドロゴの改変。
【カット4（質感の再フック）】肌の上でのばした直後のツヤ接写。この画像は静止画として完結させ、次の工程で動かす前提のため、被写体の輪郭がフレーム端で切れないようにする。
```

### カット5（10.0-12.0 CTA）
```
同一人物・同一世界観で通すこと。人物設定: 26-29歳に見える、黒髪セミロング、やや目尻の下がった一重寄りの二重、ナチュラルメイク、日本人、清潔感、生活感のある部屋。衣装: オフホワイトのリブトップス／グレーのルームウェア。場所: 自然光の入る洗面台、白いタイル、木のトレー。写真的リアリズム、自然光、9:16縦構図、被写界深度浅め、加工しすぎない肌質（毛穴とうぶ毛を残す）。禁止: 露出の高い服装、扇情的なポーズ、実在の芸能人に似せる、ブランドロゴの改変。
【カット5（CTA）】商品単体、余白多め。この画像は静止画として完結させ、次の工程で動かす前提のため、被写体の輪郭がフレーム端で切れないようにする。
```

---

## ② Grok Imagine 画像→動画プロンプト

各カットの画像をアップロードし、以下を貼る。1クリップ最大10秒（Imagine 1.0）。
被写体と動きの記述は編集しやすいよう日本語のまま残してある。指示追従が弱い時は英訳する。
動きが出ない場合は「Motion:」の動詞を強い語（drifts / unfurls / surges）に差し替える。

### カット1（0.0-1.8 / 3秒）
```
Animate this still photo. Subject: 手の甲／指先でのテクスチャ超接写。とろみが糸を引く、粒が溶ける. Motion: 極スローのマクロ寄り。カメラは動かさず被写体だけ動く. Keep the motion subtle and single-purpose — one clear movement only. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 3 seconds. 9:16 vertical.
```

### カット2（1.8-4.0 / 3秒）
```
Animate this still photo. Subject: ボトルを持つ手元。ラベルは3カット目までは寄りすぎない. Motion: ゆっくり手前に傾ける. Keep the motion subtle and single-purpose — one clear movement only. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 3 seconds. 9:16 vertical.
```

### カット3（4.0-7.5 / 4秒）
```
Animate this still photo. Subject: AI美女：洗面台の鏡ごし、頬に伸ばす手元中心（顔は3割）. Motion: 微細な呼吸・髪の揺れのみ。表情は変えない. Keep the motion subtle and single-purpose — one clear movement only. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 4 seconds. 9:16 vertical.
```

### カット4（7.5-10.0 / 3秒）
```
Animate this still photo. Subject: 肌の上でのばした直後のツヤ接写. Motion: 光が横に流れる. Keep the motion subtle and single-purpose — one clear movement only. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 3 seconds. 9:16 vertical.
```

### カット5（10.0-12.0 / 3秒）
```
Animate this still photo. Subject: 商品単体、余白多め. Motion: near-static — 静止＋わずかなパララックス。Only micro-movements are allowed (breathing, a single blink, a subtle shift of light). Nothing else moves. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 3 seconds. 9:16 vertical.
```

---

## ③ imagine agent 丸投げプロンプト（画像→動画 ＋ 編集）

画像 5 枚と一緒に、これ1つを投げる。

```
あなたは、静止画から縦型ショート動画を1本完成させる映像ディレクター兼エディターです。
YouTube・ドキュメンタリー編集で15年以上の経験を持つシニアエディターとして振る舞ってください。
入力として、同一人物・同一世界観のAI生成静止画を 5 枚渡します。
これらを「画像→動画化」し、続けて「1本の動画への編集」まで、途中で私に確認を取らず最後まで実行してください。

## 案件
- 商品: △△クレンジングバーム（クレンジング）
- 狙う悩み: メイク崩れ
- 訴求: 体温で溶けるのが早い
- 尺: 12秒 / 9:16 / 配信先: tiktok
- 採用する型: 無音テクスチャASMR型（言語に依存しないので量産が最も速く、失敗コストが低い。テクスチャ接写＋ASMRは2026年の定番で、冒頭2秒の視覚フックだけで滞在が伸びる。AI美女は『使ってる人』としてカット3以降に置くだけで成立する。）

## 登場人物（全カットで固定）
26-29歳に見える、黒髪セミロング、やや目尻の下がった一重寄りの二重、ナチュラルメイク、日本人、清潔感、生活感のある部屋。衣装: オフホワイトのリブトップス／グレーのルームウェア。場所: 自然光の入る洗面台、白いタイル、木のトレー。
カットをまたいで顔・髪型・肌の色・衣装が変化してはいけません。変化したカットは破棄して作り直してください。

## 第1工程：画像→動画（各カットを個別に生成）
各カットについて、以下の要件を満たす動画クリップを作ってください。
- 動きは1カットにつき1種類だけ。複数の動きを重ねると破綻します
- カメラは元画像のフレーミングを保持。クリップ内でカットを割らない
- 顔の構造・髪型・肌の色・衣装・商品ラベルは一切変形させない
- 音声は環境音のみ。人物にセリフを喋らせない

| # | タイムコード | 役割 | 画（何が映るか） | 動き | テロップ |
|---|---|---|---|---|---|
| 1 | 0.0-1.8 | 視覚フック | 手の甲／指先でのテクスチャ超接写。とろみが糸を引く、粒が溶ける | 極スローのマクロ寄り。カメラは動かさず被写体だけ動く | 音アリ推奨🔊 |
| 2 | 1.8-4.0 | 文脈提示 | ボトルを持つ手元。ラベルは3カット目までは寄りすぎない | ゆっくり手前に傾ける | メイク崩れの日に戻ってくるやつ |
| 3 | 4.0-7.5 | 人物投入 | AI美女：洗面台の鏡ごし、頬に伸ばす手元中心（顔は3割） | 微細な呼吸・髪の揺れのみ。表情は変えない | 体温で溶けるのが早い |
| 4 | 7.5-10.0 | 質感の再フック | 肌の上でのばした直後のツヤ接写 | 光が横に流れる | この“のび”が全部 |
| 5 | 10.0-12.0 | CTA | 商品単体、余白多め | 静止＋わずかなパララックス | 詳細はプロフィールから／#PR |

各カットの生成プロンプト（そのまま使用可）:
- カット1（3秒）: Animate this still photo. Subject: 手の甲／指先でのテクスチャ超接写。とろみが糸を引く、粒が溶ける. Motion: 極スローのマクロ寄り。カメラは動かさず被写体だけ動く. Keep the motion subtle and single-purpose — one clear movement only. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 3 seconds. 9:16 vertical.
- カット2（3秒）: Animate this still photo. Subject: ボトルを持つ手元。ラベルは3カット目までは寄りすぎない. Motion: ゆっくり手前に傾ける. Keep the motion subtle and single-purpose — one clear movement only. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 3 seconds. 9:16 vertical.
- カット3（4秒）: Animate this still photo. Subject: AI美女：洗面台の鏡ごし、頬に伸ばす手元中心（顔は3割）. Motion: 微細な呼吸・髪の揺れのみ。表情は変えない. Keep the motion subtle and single-purpose — one clear movement only. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 4 seconds. 9:16 vertical.
- カット4（3秒）: Animate this still photo. Subject: 肌の上でのばした直後のツヤ接写. Motion: 光が横に流れる. Keep the motion subtle and single-purpose — one clear movement only. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 3 seconds. 9:16 vertical.
- カット5（3秒）: Animate this still photo. Subject: 商品単体、余白多め. Motion: near-static — 静止＋わずかなパララックス。Only micro-movements are allowed (breathing, a single blink, a subtle shift of light). Nothing else moves. Camera: hold the framing of the source image; no whip pans, no cuts inside the clip. Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point. Mood: calm, natural daylight, soft contrast, editorial skincare commercial. Audio: ambient room tone only, no speech. Duration: 3 seconds. 9:16 vertical.

## 第2工程：編集（1本に組み上げる）
第1工程のクリップを、上の表のタイムコード順に接続し、次を適用してください。
1. **冒頭0-2秒**: 視覚フックとテロップを同時に立てる。商品名・ロゴはこの区間に出さない
2. **カット尺**: 平均1.2〜2.5秒。3秒を超えるカットは中で寄り／引きを作って変化を入れる
3. **テロップ**: 太字・高コントラスト・画面中央60%以内（上下のUIに隠れるため）。1カット1メッセージ
4. **音**: BGMは環境音寄りの低音量。テクスチャSFX（ぬちゃ／とろ）を0.2秒だけ強調。ナレーションなし
5. **トランジション**: 基本はストレートカット。使う場合もホイップパン/フラッシュを全体で1回まで
6. **パターンインタラプト**: 5秒に1回、SFX・ズーム・テロップ切替のいずれかで変化を作る
7. **CTA**: 最終カットに「詳細はプロフィールから／#PR」を出す
8. **書き出し**: 1080x1920 / 30fps / H.264 High / 10-14 Mbps / 音声 AAC 256-320kbps 48kHz / Rec.709 / sRGB。再圧縮が強いので細いフォント・微細グラデは潰れる。テロップは太字・高コントラストで

## 守ること（違反したら作り直し）
- 効果・効能を断定しない。化粧品の効能効果の範囲を超える表現（「シミが消える」「ニキビが治る」「美白になる」等）を映像・音声・テロップのいずれにも入れない
- 使用前後の変化を見せない／示唆する画作りをしない。この人物の肌は「成果」ではなく「世界観」です
- 架空の人物に体験談を語らせない。一人称の使用感を音声・テロップで語らせない
- 実在の人物・ブランドに似せない
- 最終カットに「AI生成」の旨を表示する（映像内表示＋投稿時のAIラベル両方）
- 広告表記 #PR をキャプションに必ず含める

## 出力
1. 完成動画（12秒、9:16）
2. 使用した編集判断の一覧（タイムコード / 編集アクション / B-roll・ビジュアル / 音声・SFX / 編集メモ の5列の表）
3. 上の「守ること」への自己チェック結果（各項目 OK/NG と根拠）
```

---

## ④ テロップ全文

| # | タイムコード | テロップ |
|---|---|---|
| 1 | 0.0-1.8 | 音アリ推奨🔊 |
| 2 | 1.8-4.0 | メイク崩れの日に戻ってくるやつ |
| 3 | 4.0-7.5 | 体温で溶けるのが早い |
| 4 | 7.5-10.0 | この“のび”が全部 |
| 5 | 10.0-12.0 | 詳細はプロフィールから／#PR |

## ⑤ 投稿キャプション

```
音アリ推奨🔊

△△クレンジングバーム｜メイク崩れが気になる日に。
・体温で溶けるのが早い
・個人差があります。パッチテストをしてから使ってください

※映像はAI生成です
#PR
```

## ⑥ 検品結果

- compliance.checkContent: **PASS**
- スキンケア禁止語: **なし**
- 記入漏れ: **なし**
- 型の固有リスク: テクスチャ接写は薬機法リスクが最も低い。テロップに効能を書かなければ実質ノーリスク
- AIラベル: **必要**（投稿時にプラットフォームのAI表示をONにする）

## ⑦ Gemini 編集プロンプト

`prompts/gemini-edit.md` を参照。この案件の穴埋め値:
- ターゲット視聴者: メイク崩れが気になっている20代後半〜30代前半
- プラットフォーム: tiktok
- コンテンツの傾向: 無音テクスチャASMR型
