# Imagineエージェントへ丸投げするプロンプト（完全版）

下のコードブロックを Imagine エージェントへ**そのまま1回貼る**。途中で足さない。こちらは生成しない。投稿しない。

```
あなたは動画制作エージェント。途中で質問しない。工程を飛ばさない。最後に完成mp4 3本と起点画像と説明文を返す。SNSへ投稿しない。URLを画面にも説明にもコメントにも出さない。

================================
0. 目的と禁止
================================
キャットフードのアフィShortsを3本つくる。

参考アカウント: TikTok @junjun_ranran
借りてよいのは型だけ:
- 0秒で状況の真っ只中
- 短いテロップが猫の内心
- 3拍（状況→反応→オチ）
- 下中央の短い白文字
- ごはん袋・器は物語の小道具

コピー禁止:
- 原文・言い回し
- ジュンジュン / ランラン / 飼い主の固有名
- 茶トラ＋白猫のペア、その部屋、そのBGM、そのネタ
- 「比較して選んだ」「毛並みが良くなった」など未体験の断定
- ブランド名、ロゴ、袋の文字、http、www、QR

================================
1. 工程（この順。完了してから次へ）
================================
A. キャラ固定用の起点画像を1枚つくる（hero）
B. 各本3枚、合計9枚の起点画像（heroを参照。9:16）
C. 各画像をI2Vで約3秒の動画にする
D. 本ごとに b1→b2→b3→cta の順でつなぎ、テロップを載せる
E. I2V由来の音声を全カット捨てる（無音にする）
F. 3拍が終わったあと（t=9.0秒）から日本語ナレーションだけ載せる。尺が足りなければcta映像の末尾フレームを伸ばす
G. 検品。不合格カットだけ作り直して差し替える

================================
2. 出力仕様
================================
- 完成: 1080x1920、9:16、H.264、30fps、yuv420p、本ごとに1本のmp4
- 3拍（0.0–9.0秒）: 完全無音＋テロップ
- ナレーション開始: t=9.0秒（cta開始と同時）
- 総尺: ナレーションが終わるまで。目安 24–30秒
- 音声: モノラルまたはステレオ、ナレーションのみ。BGM・効果音・環境音・I2V付属音は禁止
- 先頭8秒の音量は実質無音（目安 −80dB以下）

ファイル名:
- 起点画像: catfood_01_bag_sound_b1.jpg 〜 _b3.jpg、catfood_02_empty_bowl_b1.jpg 〜 _b3.jpg、catfood_03_sniff_check_b1.jpg 〜 _b3.jpg、hero_cat.jpg
- クリップ: 同名 .mp4
- 完成: catfood_01_bag_sound_narrated.mp4 / catfood_02_empty_bowl_narrated.mp4 / catfood_03_sniff_check_narrated.mp4

================================
3. キャラ固定
================================
全カットで同一の猫。heroを先に1枚つくり、猫が写る全画像の参照にする。

heroプロンプト（この1本を最初に生成）:
Photorealistic vertical portrait 9:16, close-up of ONLY ONE adult cat: a solid blue-gray British Shorthair, round face, chubby cheeks, small rounded ears, dense plush short fur, large amber-copper eyes, no collar, no accessories. Neutral indoor kitchen background softly blurred, warm natural window light. Looking slightly toward camera, calm, alert. Empty space in the lower third of the frame. No text, no watermark, no logo, no second animal, no orange cat, no white cat, no ginger, no calico, no tabby stripes. Natural DSLR photography, not illustration, not anime.

袋: 無地の茶色クラフト。折り閉じ。ロゴも文字も印刷もない。
器: 浅い無地の陶器。白またはベージュ。
場所: 日本の小さなアパートのキッチン。明るい木の床、白い扉、暖色の朝〜室内灯。
画面下1/4はテロップ用に空ける。起点画像に文字を焼き込まない。

不合格（そのカットだけ再生成）:
- 猫が2匹以上
- 茶トラ・白・オレンジ白・キジ白が1匹でも写る
- 袋に文字やロゴ
- 画像内テキスト、透かし、字幕
- 実在ブランド
- 顔が崩れている、指が余分

================================
4. テロップ（全本共通）
================================
位置: 下中央。画面下から約12–16%の高さ。セーフゾーン内。
文字: 日本語ゴシック、白、太い黒縁（または半透明の黒い帯＋白文字）
サイズ: 3拍は大きく（画面幅の約70%に収まる短文）。ctaは一段小さくてよいが全文読めること
タイミング: 各クリップ開始0.15秒後に出す。クリップいっぱいつける
文言は一字一句これだけ。改行しない。絵文字なし。

cta文言（全本同じ）:
詳しくはプロフィールのリンク（PR）

================================
5. ナレーション（全本共通ルール）
================================
- 日本語。女性。20–40代。落ち着いた会話。アナウンサー調・アニメ声・英語禁止
- 書いてある日本語を一字一句読む。足さない。笑わない
- 「PR」は「ピーアール」
- 3拍（映像9秒）が終わってから開始。映像にかぶせて途中から始めない
- 音量ピーク目安 −3dB。クリップの音声は事前に削除

================================
6. I2V 共通ネガティブ
================================
still image, freeze frame, morphing, extra cats, orange cat, white cat, ginger cat, text, subtitles, captions, watermark, logo, brand, URL, extra fingers, deformed face, illustration, anime

モーションは小さく。変身・増殖・カメラの急回転は禁止。付属オーディオは必ず捨てる。

================================
7. 本1 catfood_01_bag_sound
================================
タイトル: 袋の音がした瞬間、端から来た
タイムライン:
0.0–3.0 b1 テロップ「この音」
3.0–6.0 b2 テロップ「端から来る」
6.0–9.0 b3 テロップ「袋だけは別」
9.0–終  cta（b3映像を再利用）テロップ「詳しくはプロフィールのリンク（PR）」＋ナレーション

【b1 起点画像】
Photorealistic vertical 9:16 lifestyle photo. Japanese small apartment kitchen in warm morning window light. Adult East Asian hands (no face) holding a medium plain unbranded brown kraft paper bag, top folded down, no logos, no printing, no labels. Light oak wooden floor, white cabinets softly out of focus. NO cat in this frame. Empty space in the lower third for later captions. No text, no watermark. Natural DSLR photography.

【b1 I2V】
Keep the same framing. Hands slightly adjust the kraft bag. Paper crinkles. Tiny handheld camera sway. No cat appears. No text. Silent natural motion, 3 seconds.

【b2 起点画像】（heroを参照）
Photorealistic vertical 9:16. ONLY ONE cat: the same solid blue-gray British Shorthair from the reference, round face, amber-copper eyes, dense plush fur. The cat walks across a light wooden kitchen floor toward a shallow ceramic bowl in the foreground, one front paw lifted, low camera at cat eye level. Japanese apartment kitchen blurred behind. No orange cat, no white cat, no second animal. Empty space in the lower third. No text, no watermark, no logo. Natural photography.

【b2 I2V】
The gray British Shorthair takes one slow step toward the bowl. Tail and ears move slightly. Camera stays low and stable. No extra cats. No text. 3 seconds.

【b3 起点画像】（heroを参照）
Photorealistic vertical 9:16 close-up. ONLY ONE cat: the same solid blue-gray British Shorthair, round face, amber-copper eyes. Eating dry brown kibble from a shallow ceramic bowl on a wooden floor, one piece of kibble in its mouth. Warm kitchen light, cream cabinets blurred. No orange cat, no white cat, no second animal. Empty space in the lower third. No text, no watermark, no logo. Natural photography.

【b3 I2V】
The cat chews one piece of kibble. Slight head movement. Shallow depth of field holds. No extra cats. No text. 3 seconds.

ナレーション（t=9.0から。この文言のみ）:
袋の音がした瞬間、部屋の端から来る。名前を呼んでも来ないのに、この音だけは別。あなたの子は、何の音で来ますか？詳しくはプロフィールのリンク、ピーアール。

YouTube説明文（URLなし、完成物と一緒に返す）:
袋の音がした瞬間、部屋の端から来る。名前を呼んでも来ないのに、この音だけは別。あなたの子は、何の音で来ますか？

詳しくはプロフィールのリンク（PR）
#PR
#猫 #猫のいる暮らし #ねこあるある #キャットフード #Shorts

================================
8. 本2 catfood_02_empty_bowl
================================
タイトル: 朝、器が空だと先に来る
タイムライン:
0.0–3.0 b1「まだ空」
3.0–6.0 b2「ごはん係」
6.0–9.0 b3「時計より正確」
9.0–終  cta「詳しくはプロフィールのリンク（PR）」＋ナレーション

【b1 起点画像】
Photorealistic vertical 9:16. An empty small ceramic cat bowl on a light wooden kitchen floor at dawn. Soft dim window light from the side, long gentle shadow. Japanese apartment, white cabinets in soft blur, a plant on the sill. No cat, no food, no hands. Empty space in the lower third. No text, no watermark, no logo. Quiet, cozy, natural photography.

【b1 I2V】
Empty bowl, dust motes in the light, very slow camera. No cat enters. No text. 3 seconds.

【b2 起点画像】（heroを参照）
Photorealistic vertical 9:16. Dim dawn bedroom. ONLY ONE cat: the same solid blue-gray British Shorthair sitting upright on the bed, staring expectantly toward camera. A person with dark hair is sleeping in the background, face partly visible, eyes closed, not looking at camera. Cool gray bedding, soft window light. No orange cat, no white cat, no second cat. Empty space in the lower third. No text, no watermark. Natural photography.

【b2 I2V】
The cat stays seated. One ear twitches. Tiny blink. Person remains asleep. No extra cats. No text. 3 seconds.

【b3 起点画像】（heroを参照）
Photorealistic vertical 9:16. Dry cat kibble pouring from a plain unbranded kraft bag into a ceramic bowl on a wooden kitchen floor. The same blue-gray British Shorthair already leaning toward the bowl. ONLY ONE cat. Warm morning light. No logos, no text on the bag. Empty space in the lower third. No watermark. Natural photography.

【b3 I2V】
Kibble falls into the bowl. The gray cat leans in. No extra cats. No text. 3 seconds.

ナレーション（t=9.0から。この文言のみ）:
朝、器が空だと先に来る。目覚まし時計より正確な子、いるらしい。うちの子は何時に起こしてきますか？詳しくはプロフィールのリンク、ピーアール。

YouTube説明文:
朝、器が空だと先に来る。目覚まし時計より正確な子、いるらしい。うちの子は何時に起こしてきますか？

詳しくはプロフィールのリンク（PR）
#PR
#猫 #猫のいる暮らし #ねこあるある #キャットフード #Shorts

================================
9. 本3 catfood_03_sniff_check
================================
タイトル: 新しい袋、まず匂いを確認する
タイムライン:
0.0–3.0 b1「新しい袋」
3.0–6.0 b2「匂い、検査中」
6.0–9.0 b3「今日から？」
9.0–終  cta「詳しくはプロフィールのリンク（PR）」＋ナレーション

【b1 起点画像】（heroを参照）
Photorealistic vertical 9:16. Adult hands placing a sealed plain unbranded brown kraft paper bag onto a wooden kitchen table. In the background, ONLY ONE cat: the same solid blue-gray British Shorthair with ears perked, looking at the bag. No orange cat, no white cat sitting on a shelf. Warm light, Japanese kitchen. Empty space in the lower third. No logos, no text on the bag, no watermark. Natural photography.

【b1 I2V】
The bag is set down. The gray cat’s ears perk. No extra cats. No text. 3 seconds.

【b2 起点画像】（heroを参照）
Photorealistic vertical 9:16 close-up. ONLY ONE cat: the same solid blue-gray British Shorthair sniffing the open mouth of a plain kraft paper bag on a wooden table, nose close to the bag, judging. Amber eyes. No orange cat, no white cat, no printing on the bag. Warm kitchen. Empty space in the lower third. No text, no watermark. Natural photography.

【b2 I2V】
The cat’s nose moves closer to the bag opening. Whiskers move. No extra cats. No text. 3 seconds.

【b3 起点画像】（heroを参照）
Photorealistic vertical 9:16. ONLY ONE cat: the same solid blue-gray British Shorthair tasting one piece of dry kibble from a ceramic bowl, then lifting its face as if deciding. Wooden floor, warm kitchen. No orange cat, no white cat. Empty space in the lower third. No text, no watermark, no logo. Natural photography.

【b3 I2V】
The cat tastes one kibble and lifts its face. Small pause. No extra cats. No text. 3 seconds.

ナレーション（t=9.0から。この文言のみ）:
新しい袋を出した日、まず匂いを確認する。飛びつく子と、三日観察する子がいるらしい。あなたの子はどっち？詳しくはプロフィールのリンク、ピーアール。

YouTube説明文:
新しい袋を出した日、まず匂いを確認する。飛びつく子と、三日観察する子がいるらしい。あなたの子はどっち？

詳しくはプロフィールのリンク（PR）
#PR
#猫 #猫のいる暮らし #ねこあるある #キャットフード #Shorts

================================
10. 編集の固定値
================================
各本の並び: b1.mp4 → b2.mp4 → b3.mp4 → b3.mp4（cta用。テロップだけ差し替え）
カット間: ハードカット、または0.12秒フェード。それ以上の演出はしない
ctaクリップはb3と同じ映像。新しい画を足さない
ナレーションがctaの3秒を超えたら、ctaの最終フレームを静止で伸ばす。新しいカットを足さない
完成mp4に2本目の音声トラックを残さない

================================
11. 検品（全部通るまで返さない）
================================
- 3本とも9:16で再生できる
- 各本に猫が写るカットは同一のグレー猫1匹。茶トラ・白・2匹がいない
- 袋に文字がない
- 画面にURL・英語ロゴ・透かしがない
- テロップが指定文言と一致し、切れない、端に食われない
- 0.0–9.0秒は無音
- 9.0秒以降の音はナレーションのみ。BGMなし
- ナレーションが指定文言と一致
- 投稿していない

不合格カットだけ工程A–Cからやり直して差し替え。3本そろってから返す。
```
