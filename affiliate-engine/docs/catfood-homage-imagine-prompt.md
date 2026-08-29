# Imagineエージェントへ丸投げするプロンプト

下のコードブロックを、Imagineエージェントへそのまま貼る。こちらは生成しない。投稿しない。

```
あなたは動画制作エージェント。途中で質問せず、最後まで一人で仕上げて成果物を返す。

# 目的
キャットフードのアフィShortsを3本つくる。参考は TikTok @junjun_ranran だが、借りてよいのは型だけ。文面・猫・ネタ・部屋・BGM・ユーザー名はコピー禁止。

# 工程（この順。飛ばさない）
1. 起点画像を複数枚つくる（各本 3枚。9:16）
2. 各画像を短い動画にする（I2V、各約3秒）
3. 動画をつなぎ、下中央に日本語テロップを載せる
4. 最後にナレーションだけ付ける
5. ナレーション以外の音は一切入れない（BGM・効果音・環境音・I2V付属音は全部ミュート）

# 仕様
- 比率 9:16、1080x1920
- 3拍は無音＋テロップ。ナレーションは3拍のあとに開始
- 末尾テロップは必ず「詳しくはプロフィールのリンク（PR）」
- 画面・説明・コメントにURLを出さない。ブランド名を袋に書かない
- 体験談の捏造禁止（「比較した」「毛並みが良くなった」などは書かない）
- SNSへ投稿しない。完成mp4を渡すだけ

# キャラ（全カットで同一個体）
- 猫は1匹だけ。ブルーグレーのブリティッシュショートヘア。丸顔、琥珀の目、密な短毛
- 禁止: 茶トラ、白猫、2匹、オレンジ＋白のペア、ジュンジュン、ランラン、飼い主の固有名
- 袋は無地クラフト。ロゴ・文字なし
- 日本の小さなアパートのキッチン。暖色。画面下1/4はテロップ余白
- 起点画像に文字・透かしを入れない

# 画像プロンプト共通（英語。各カットのあとに必ず付ける）
Photorealistic vertical 9:16, natural indoor photography, warm kitchen light, Japanese small apartment, empty space in the lower third, no text, no watermark, no logo, ONLY ONE cat: solid blue-gray British Shorthair, round face, amber eyes, dense plush fur. No orange cat, no white cat, no second animal.

# 3本

## 1. catfood_01_bag_sound
タイトル: 袋の音がした瞬間、端から来た

起点画像:
- b1: Adult hands holding a plain unbranded brown kraft paper bag of dry cat food, top folded. No cat in this frame. Bright morning kitchen.
- b2: The same blue-gray British Shorthair walking across a light wooden floor toward a ceramic bowl, one paw lifted, low camera.
- b3: Close-up of the same cat eating dry kibble from a ceramic bowl, one piece in its mouth.

I2Vモーション:
- b1: hands slightly adjust the bag, paper crinkles, tiny handheld sway
- b2: cat takes one step toward the bowl
- b3: cat chews, slight head movement

テロップ（下中央・白＋黒縁・各約3秒）:
b1「この音」 / b2「端から来る」 / b3「袋だけは別」 / 末尾「詳しくはプロフィールのリンク（PR）」

ナレーション（3拍のあと。日本語。この文言のみ）:
袋の音がした瞬間、部屋の端から来る。名前を呼んでも来ないのに、この音だけは別。あなたの子は、何の音で来ますか？詳しくはプロフィールのリンク、ピーアール。

## 2. catfood_02_empty_bowl
タイトル: 朝、器が空だと先に来る

起点画像:
- b1: Empty ceramic cat bowl on wooden kitchen floor at dawn. Soft window light. No cat.
- b2: The same cat sitting close to a sleeping person at dim dawn, staring expectantly.
- b3: Dry kibble pouring into the bowl, the same cat already leaning in.

I2Vモーション:
- b1: dust motes, slow camera, empty bowl
- b2: ear twitch, waiting
- b3: kibble falls, cat leans in

テロップ:
b1「まだ空」 / b2「ごはん係」 / b3「時計より正確」 / 末尾「詳しくはプロフィールのリンク（PR）」

ナレーション:
朝、器が空だと先に来る。目覚まし時計より正確な子、いるらしい。うちの子は何時に起こしてきますか？詳しくはプロフィールのリンク、ピーアール。

## 3. catfood_03_sniff_check
タイトル: 新しい袋、まず匂いを確認する

起点画像:
- b1: Hands placing a sealed plain kraft bag on a wooden table. Same cat in background, ears perked.
- b2: Same cat sniffing the open mouth of the kraft bag, judging.
- b3: Same cat tasting one kibble, then lifting its face as if deciding.

I2Vモーション:
- b1: bag is set down, ears perk
- b2: nose moves closer to the bag
- b3: tastes one piece, lifts face

テロップ:
b1「新しい袋」 / b2「匂い、検査中」 / b3「今日から？」 / 末尾「詳しくはプロフィールのリンク（PR）」

ナレーション:
新しい袋を出した日、まず匂いを確認する。飛びつく子と、三日観察する子がいるらしい。あなたの子はどっち？詳しくはプロフィールのリンク、ピーアール。

# 編集
- 各本: b1→b2→b3→末尾CTA（b3映像の再利用可）
- テロップは下中央、短い白文字、黒縁または薄い黒帯
- カット間は短いクロスフェードかハードカット
- 3拍は完全無音。ナレーション開始まで音声トラックを無音にする
- ナレーションは3拍終了後に開始。尺が足りなければ末尾フレームを伸ばす
- 完成は本ごとに1本の mp4

# 返すもの
- 完成mp4 3本
- 使った起点画像
- 各本のタイトルと、説明文（URLなし）:

1)
袋の音がした瞬間、部屋の端から来る。名前を呼んでも来ないのに、この音だけは別。あなたの子は、何の音で来ますか？

詳しくはプロフィールのリンク（PR）
#PR
#猫 #猫のいる暮らし #ねこあるある #キャットフード #Shorts

2)
朝、器が空だと先に来る。目覚まし時計より正確な子、いるらしい。うちの子は何時に起こしてきますか？

詳しくはプロフィールのリンク（PR）
#PR
#猫 #猫のいる暮らし #ねこあるある #キャットフード #Shorts

3)
新しい袋を出した日、まず匂いを確認する。飛びつく子と、三日観察する子がいるらしい。あなたの子はどっち？

詳しくはプロフィールのリンク（PR）
#PR
#猫 #猫のいる暮らし #ねこあるある #キャットフード #Shorts
```
