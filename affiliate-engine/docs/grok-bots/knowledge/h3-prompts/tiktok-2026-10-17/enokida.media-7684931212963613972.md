# money_enokida.media_7684931212963613972.mp4 – H3 prompts

- Source: `C:\work\h3prompt\in\tiktok-2026-10-17\money_enokida.media_7684931212963613972.mp4`
- Probe: 8.601 s, 1080×1920, 60 fps, H.264 + AAC stereo 44.1 kHz. Scene-detect cuts: none. True hard cuts: 0. Shots: 1.
- Reference images supplied: none. Character swap: none.

| seg | start–end | duration | `<Video 1>` file |
|---|---|---|---|
| seg_01 | 0.00–8.60 | 8.60 s | `C:\work\h3prompt\out\money_enokida.media_7684931212963613972\segments\seg_01.mp4` |

## Recommended: Ref2VA

映像は最初のフレームから最後まで同一の文字カードで、カメラの動きもカットもない。`segments\seg_01.mp4` を `<Video 1>` として渡すと、その「動かない時間構造」を最も忠実にロックできる。参考画像は未供給なので、カードの文言は Ref2VA / T2VA の本文に書く。

## seg_01 (0.00–8.60)

### Analysis (日本語)

**映像タイプ。** 縦 9:16、8.60 秒、1080×1920、60 fps。ショットは1つ。ハードカットなし、ディゾルブなし、速度変化なし。密フレーム（4 fps、d_0001＝0.00 秒から d_0034＝8.25 秒）と疎グリッドは、見出し・①〜⑦・フッターが最初のコマから全部出たまま。0.00 / 2.00 / 4.00 / 6.00 / 8.20 秒の生フレームを比較すると、最適合わせは移動 0 px、チャンネル平均のずれは 0.1 未満。差が 20 を超える画素は全体の 0.7% で、文字の縁に集中する。これは H.264 のリンギングであり、パン・ズーム・人物の動作ではない。運動から静止への段差はない。バーストもない。映像タイプは **A（一本の完全ロックオフ静止）**。B の二状態（HARD LOCK ↔ INSTANT BURST）は使わない。静止が唯一の状態なので、禁止は時間軸・カメラ・禁止欄の三箇所に繰り返す。C（マルチショット）ではない。

**シーン。** 暗い室内写真の全面に、フラットな図版カードが載っている。左に格子窓、天井に裸電球が二つ（左上は大きく、右上は小さい）、中央に着座した人物、明るい天板、画面左中段に暗い器、フッター下にオフィスチェアの脚と暗い床。会場名（カフェか小オフィスか）は写真だけでは断定しない。TikTok のユーザー名、いいね、進捗バー、透かしは見えない。

**人物（画外の行為者を含む）。** 話す人も、画外から手を入れる人もいない。着座人物は背景写真の一部で、バーに顔の大半を隠されている。性別・年齢・手元の端末は断定しない。服は暗い。8.60 秒のあいだ姿勢は変わらない。

**因果の連鎖。** 視覚の状態変化はゼロ。トリガーは「完成したカードを読ませる」という編集意図だけで、画面内では誰も動かない。00:00.00 に見出し『こんな会社、終わる』、①〜⑦、フッター『あなたの会社は何個当てはまりますか？ / 理由はキャプションで。』が同時に存在し、00:08.60 まで同じ。項目が順に出る、という仮説は否定された。音だけが 7.5 秒付近の最後のパルスのあと減衰し、8.5 秒ではほぼ無音。画面はそれに反応しない。

**カメラ割り。**

| 区間 | ショットサイズ | カメラ位置 | 動き | 動機 |
|---|---|---|---|---|
| 00:00.00–00:08.60 | 縦の全面グラフィック（人物の寄りではない） | カードに正対。水平は傾いていない。地平線の回転はなく、カメラ Roll でも人物の寝転びでもない | 振幅なし、速度なし、固定 | 7 項目を読ませるため。ビートには合わせない |

**編集エフェクト。** フリーズフレーム、白閃、漫画線、擬音文字、RGB グリッチ、パンチイン、なし。静止はギャグ用のフリーズではなく、クリップ全体が1枚のカード。入点・長さ・重ね・戻りの四要素は該当なし。

**リズム。** 固定拍。onset 22 個、間隔平均 0.357 秒（ちょうど 168 BPM）、std/mean＝0.022。スペクトルは低域の縦縞が等間隔。自由散板ではない。168 BPM と書いてよい。ただし画面の切替先がないので、拍に合わせたカット編集ではない。強 onset はすべて楽曲側。

| onset（秒） | 強度 | 画面 | カットやエフェクト |
|---|---|---|---|
| 3.96 / 4.31 / 4.66 | S | カードは無変化 | なし |
| 5.02 / 5.74 / 6.10 | H | カードは無変化 | なし |
| 7.16 | S | カードは無変化 | なし |
| 7.52（弱） | . | 最後の検出パルス。以降グリッドなし | なし |

RMS（0.5 秒）は 0.0 秒からすでに 0.098 で、音楽は頭から入っている。最大は 4.0 秒の 0.164。7.5 秒は 0.130。8.0 秒は 0.065。8.5 秒は 0.0005。エネルギー峰に対応する画面イベントはない。密度は毎秒 2〜3 個でほぼ平坦（168 BPM の格子そのもの）。8 秒台だけ n＝0。

**音の結論。** BGM あり。根拠は、低域優勢（low 65 / mid 17 / hi 0.5）、等間隔 onset、スペクトルのキック格子、mean -19.4 dB / max -2.7 dB。明瞭な発話はない。口は動かず、子音帯域がほぼ無い。仮説の「発話なし」は支持される。カフェの皿音や部屋鳴りは分離できない。同期音はなし。音楽は non-diegetic のみ。曲名・歌詞は書かない。

**推測と未確認。**

- 偶数バー（②④⑥）は奇数バーより灰みがかった青で、写真がわずかに透けるように見える。奇数バーと赤帯はほぼ不透明。透過の正確なアルファは未計測。
- 着座人物の手元の暗い器はマグカップに見える。スマホやノートを見ている、という仮説はフレームでは確定できない。
- 中域エネルギーが少しあるため、極薄の非言語ハミングが混ざる可能性はある。歌詞として聞き取れる発話は、スペクトルと口の静止からは支持されない。
- ユーザー仮説（会社員のお金・働き方、静止画1枚、見出しと①〜⑦、発話なし、カットなし、オチはキャプションへ）は、文言と構造については支持された。「0–2 秒は見出しだけ」は支持されない。見出しもリストも最初から全部出ている。

### Ref2VA  ★recommended

Upload `segments\seg_01.mp4` as `<Video 1>`. No `<Picture N>`. No `<Audio N>`.

```text
subject_definitions:
<Subject 1> is the full-frame vertical text card: a dark-red header banner, seven inset two-line bars, and a dark-red footer banner. It is bold white Japanese gothic type with no outline and no drop shadow. The card is already complete. It is not a person and it does not animate.
<Subject 2> is the still photograph underneath the card: a dim low-key interior, a multi-pane window at frame-left, two warm exposed bulbs on a dark ceiling, a seated person in dark clothes whose face is mostly hidden by the bars, a light tabletop, a dark mug at frame-left around the middle bars, and an office-chair base on a dark floor below the footer. <Subject 2> is a frozen photograph, not a performer.
<Video 1> is the source video that defines the target video's shot structure, motion path, and pacing: an 8.60-second vertical hold of this same finished card with absolute zero camera movement and zero subject movement. <Video 1> is used only for temporal structure; discard H.264 edge flicker and do not invent motion, cuts, a presenter, or a beat-synced text reveal.

summary:
[static checklist card + video timing reference] Recreate an 8.60-second 9:16 still in which <Subject 1> stays fully readable on top of <Subject 2> from the first frame to the last. <Video 1> supplies only the hold: one locked frame, no cuts, no pushes, no sequential reveals. The 168 BPM bed is audience-only and must not move the picture.

retention_analysis:
<Subject 1> (appears in [Shot 1] for the entire 8.60s): fully_preserved - every banner, every bar, every Japanese glyph, the circled numbers, the arrows, the yellow hand emoji, and the red/blue colors stay exactly as written below.
<Subject 2> (appears in [Shot 1] for the entire 8.60s, visible in the margins, the gaps, above the header, and below the footer): fully_preserved - the interior photograph stays frozen, including the seated pose, the mug, the bulbs, and the chair base.
<Video 1> (governs the whole video): reference - keep the single locked hold and the 8.60-second duration; discard compression flicker and any temptation to treat the musical pulse as a cut or a zoom.

detailed_description:
The target video uses a flat social-graphic card over a dim photorealistic interior still. Vertical 9:16. Duration 8.60 seconds. One continuous locked-off shot. There is no INSTANT BURST. The only camera state is ABSOLUTE ZERO MOTION for the entire timeline.

[Shot 1] A vertical full-frame graphic plate, camera square to the card, horizon level, no dutch angle. <Subject 1> fills the frame from the first instant: a full-bleed dark-red header (flat fill near RGB 90, 30, 30) with centered bold white type reading こんな会社、終わる ; then seven left-aligned inset bars that stop short of both side edges so the photograph shows in the margins, stacked with narrow gaps, odd bars ①③⑤⑦ a saturated deep blue near RGB 40, 40, 145 and even bars ②④⑥ a muted slate blue near RGB 100, 120, 140; each bar has two white lines, a circled number on line one and a right arrow at the start of line two. Exact on-screen copy, top to bottom: ① 人が辞めるたびに、 / → 辞めた人の悪口大会が始まる。 / ② 「人手不足」と言いながら、 / → 人が辞める理由を理解しない。 / ③ 会議は長い。 / → 決定は遅い。責任者はいない。 / ④ 現場は疲弊している。 / → 上は数字しか見ていない。 / ⑤ 問題が起きると、 / → 原因探しより犯人探しが始まる。 / ⑥ ビジョンだけ立派。 / → 現場は冷めてる。 / ⑦ 頑張る人ほど辞めて、 / → 残る人ほど文句を言う。 The footer is a full-bleed dark-red banner matching the header, with a yellow right-pointing hand emoji at the left of the first line and two centered white lines: あなたの会社は何個当てはまりますか？ and 理由はキャプションで。 <Subject 2> remains the dim interior behind those gaps: warm bulbs, window, seated figure, mug, table, chair base. Nothing triggers a change. <Subject 1> does not type on, wipe, fade, bounce, or highlight. <Subject 2> does not blink, breathe, turn, or reach. The camera holds steady at none amplitude and none speed, motivated only by reading time, not by the beat. No zoom, no push, no pull, no pan, no tilt, no roll, no orbit, no truck, no handheld shake, no parallax, no drift, no Ken Burns, no residual momentum. Current sound: no diegetic voice, no room tone, no foley. At 00:07.52 the non-diegetic bed gives its last pulse and starts to decay; the picture does not react. At 00:08.50 the music layer is silent and the card is still the same plate, held through the end of the shot.

TIME BUDGET: 00:00.00–00:08.60 STATIC HOLD, camera zero, card already complete. 00:07.52 last musical pulse, picture unchanged. 00:08.50–00:08.60 music-layer silence, picture unchanged.
FINAL READ: FULL CARD ALREADY ON → HOLD → MUSIC TAIL → STILL HOLD.
Do not reveal the seven lines one by one. Do not cut on the kick. Do not punch in on the footer.

overall_soundscape:
No diegetic ambience, no voice, no footsteps, no mug clink, no UI click, no cafe chatter. The picture is silent for all 8.60 seconds. Do not add room tone under the bed.

non_diegetic_music:
A bass-forward electronic beat at a fixed 168 BPM, dry kick on every pulse (one pulse each 0.357 seconds), almost no bright cymbal air, no intelligible vocal and no lyrics. Moderate level, about -19 dB average with peaks near -3 dB. It is already playing at the first frame, does not restart, and does not sync any picture change. After the last pulse near 00:07.52 the bed decays, and from 00:08.50 to 00:08.60 the music layer is explicit silence. No song title. No artist. No extra melody.
```

### T2VA

No reference image and no supplied audio file. Text must carry the card.

```text
subject_definitions: <Subject 1> is a finished vertical text card, not a person: full-bleed dark-red header, seven inset two-line bars (odd bars deep blue, even bars muted slate blue), full-bleed dark-red footer, bold white Japanese gothic, circled numbers ① to ⑦, a right arrow on every second line, and a yellow right-pointing hand emoji on the footer. <Subject 2> is the frozen photograph behind it: one seated person in dark clothes, face mostly covered by the bars, hands near a light table, a dark mug at frame-left, an office-chair base at the bottom. No second person. No off-camera actor. Vertical 9:16. Duration 8.60 seconds.

environment_definition: A dim low-key interior filling the frame under the card. Multi-pane window at frame-left. Dark ceiling. Two warm exposed bulbs, the larger one upper-left of the headline and a smaller one upper-right. Light tabletop across the middle. Dark floor below the footer. No extra signage, no weather, no TikTok username, no like button, no progress bar, no watermark.

lighting_definition: The photograph is underexposed and warm only where the two bulbs burn. Shadows stay crushed. The red banners and blue bars are flat graphic fills, not lit by the bulbs, and they do not flicker. Color and exposure are constant from 00:00.00 to 00:08.60.

integrated_multimodal_description: One locked graphic hold for 8.60 seconds with no payoff motion: the checklist is complete at the open and is still complete at the end. [Shot 1] The card is already full-frame and readable, header through footer, over the frozen interior. Header copy: こんな会社、終わる. Bar copy, in order: ① 人が辞めるたびに、 → 辞めた人の悪口大会が始まる。 ② 「人手不足」と言いながら、 → 人が辞める理由を理解しない。 ③ 会議は長い。 → 決定は遅い。責任者はいない。 ④ 現場は疲弊している。 → 上は数字しか見ていない。 ⑤ 問題が起きると、 → 原因探しより犯人探しが始まる。 ⑥ ビジョンだけ立派。 → 現場は冷めてる。 ⑦ 頑張る人ほど辞めて、 → 残る人ほど文句を言う。 Footer copy, two lines: あなたの会社は何個当てはまりますか？ / 理由はキャプションで。 The seated figure does not move. No diegetic sound. [00:07.5] The non-diegetic bed gives its last pulse and decays; the pixels do not change. [00:08.5] The music layer is silent; the same card remains through the end.

camera_direction: Locked-off, square to the card, eye-level to the graphic, horizon level. Baseline shake: none. From 00:00.00 to 00:08.60 the camera holds at none amplitude and none speed, motivated by reading time. Forbidden: zoom, push, pull, pan, tilt, roll, orbit, truck, handheld, parallax, drift, Ken Burns, snap zoom, slow motion.

editing: One unbroken take. No hard cuts, no dissolves, no speed ramps, no white flash, no punch-in, no freeze-frame gag, no manga overlay, no kinetic type. The still is the whole video, not a hold inserted inside action. No N-beat. Do not land a cut on any musical accent.

performance: There is no actor. The seated figure holds one photographic pose with no blink, no breath, no nod, and no lip movement. The blunt tone lives only in the written lines. No smile, no posed reaction, no lip-sync.

body_mechanics: No action, so no wind-up and no release. Do not invent a gesture. Hands, mug, chair, and head stay where the first frame put them. No floating, no weight shift.

costume_hair_physics: Hair, dark clothing, and the chair do not move. The type does not bounce, track, fade, or cast a new shadow. Nothing animates independently.

negative_constraints: No extra people, no presenter walking in, no extra props, no phone UI, no watermark, no subtitles beyond the designed card, no translation of the Japanese, no rewritten copy, no missing item, no eighth item, no sequential text reveal, no highlight hopping down the list, no ken burns, no zoom, no pan, no tilt, no roll, no drift, no handheld, no cut, no flash, no manga, no face animation, no identity change, no slow motion. The picture must ignore the 168 BPM pulse.

overall_soundscape: No diegetic ambience, no voice, no foley, no cafe chatter, no chair creak. The picture is silent for all 8.60 seconds.

non_diegetic_music: A bass-forward electronic beat at a fixed 168 BPM with a dry kick every 0.357 seconds, almost no bright cymbals, and no intelligible vocal. Already playing at frame one, moderate level, no restart. Last pulse near 00:07.5, then a decay. From 00:08.5 to 00:08.6 the music layer is explicit silence. No song title and no lyrics. The beat must not drive cuts or zooms.
```

### I2VA

`<Picture 1>` = `frames\seg_01_first.jpg` (first frame, universal visual anchor).

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

subject_definitions: <Subject 1> is the finished text card already printed on <Picture 1>. <Subject 2> is the dim interior photograph already behind that card on <Picture 1>, including the seated figure. <Picture 1> is the sole authority for faces, clothing, type, colors, and layout. Do not redesign them. Vertical 9:16. Duration 8.60 seconds.

visual_anchor: <Picture 1> is the universal visual anchor for the entire target video. It defines the card's exact Japanese copy, circled numbers, arrows, yellow hand emoji, red banners, blue and slate bars, margins, and the dim interior, bulbs, window, table, mug, seated pose, and chair. Whenever the target video needs to decide what any glyph, color, prop, or background looks like, it must follow <Picture 1>.

integrated_multimodal_description: One 8.60-second locked hold of <Picture 1>. No motion payoff. [Shot 1] Open already on <Picture 1>, every line of the checklist already visible, the seated figure already still. No diegetic sound. [00:07.5] The non-diegetic bed gives its last pulse and decays; the frame stays identical to <Picture 1>. [00:08.5] The music layer is silent; the frame still matches <Picture 1> through the end.

camera_direction: Locked-off and square to the card, matching <Picture 1>. None amplitude, none speed, for the entire 8.60 seconds, motivated by reading time. No zoom, push, pull, pan, tilt, roll, orbit, truck, handheld, parallax, drift, or Ken Burns.

editing: One unbroken take. No cuts, no dissolves, no speed ramps, no flash, no punch-in, no kinetic type, no sequential reveal. The still is the whole video.

performance: No actor performance. The seated figure does not blink, breathe, or move the mouth. No lip-sync.

body_mechanics: No wind-up and no gesture. Every body part stays in the pose locked by <Picture 1>.

costume_hair_physics: Hair, clothes, and type stay frozen as printed on <Picture 1>. Nothing settles because nothing moved.

negative_constraints: Do not retype, translate, restack, or animate the Japanese on <Picture 1>. No extra people, no extra props, no watermark, no subtitles, no highlight hop, no ken burns, no zoom, no pan, no tilt, no roll, no drift, no cut, no flash, no face motion. The 168 BPM bed must not move the picture.

overall_soundscape: No diegetic ambience, no voice, no foley. The picture is silent for all 8.60 seconds.

non_diegetic_music: A bass-forward electronic beat at a fixed 168 BPM, dry kick every 0.357 seconds, almost no bright cymbals, no intelligible vocal. Already playing at frame one. Last pulse near 00:07.5, then decay. From 00:08.5 to 00:08.6 the music layer is explicit silence. The beat does not drive picture changes.
```

### FL2VA

`<Picture 1>` = `frames\seg_01_first.jpg`. `<Picture 2>` = `frames\seg_01_last.jpg`. The two frames are the same card.

```text
subject_definitions: <Subject 1> is the text card locked by <Picture 1> and <Picture 2>. <Subject 2> is the dim interior and seated figure locked by those same frames. The pictures are the sole authority for identity, costume, type, and layout. Vertical 9:16. Duration 8.60 seconds.

visual_anchor: <Picture 1> is the first frame and the opening anchor. <Picture 2> is the last frame. They show the same finished checklist card. The path between them is a hold, not a transformation. Every glyph, color, and prop must match both pictures.

integrated_multimodal_description: A single continuous path from <Picture 1> to <Picture 2> with no visible change, because the last frame is the same locked card as the first. [Shot 1] Open on <Picture 1>: header, seven bars, and footer already complete, seated figure already still, no diegetic sound. The camera does not travel. [00:07.5] The non-diegetic bed gives its last pulse and decays; pixels stay on <Picture 1>. [00:08.5] The music layer is silent and the frame has converged to <Picture 2>, which matches <Picture 1>, and it stays there through the end.

camera_direction: Locked-off, square to the card, matching both pictures. None amplitude and none speed for all 8.60 seconds, motivated by reading time. No zoom, push, pull, pan, tilt, roll, orbit, truck, handheld, parallax, drift, or Ken Burns.

editing: One unbroken take. No cuts, no dissolves, no morph from <Picture 1> into a different layout, no speed ramp, no flash, no kinetic type. End exactly on <Picture 2>.

performance: No performance change between the frames. No blink, no lip-sync, no new expression.

body_mechanics: No wind-up. The body does not travel toward a new pose. The pose in <Picture 2> is the pose in <Picture 1>.

costume_hair_physics: No cloth or hair motion along the path. Type does not fade in or out.

negative_constraints: Do not invent intermediate states, a line-by-line reveal, a camera move, a face change, a translation, a watermark, or a cut. Do not treat <Picture 2> as a new composition. No ken burns. The beat must not move the picture.

overall_soundscape: No diegetic ambience, no voice, no foley. The picture is silent for all 8.60 seconds.

non_diegetic_music: A bass-forward electronic beat at a fixed 168 BPM, dry kick every 0.357 seconds, almost no bright cymbals, no intelligible vocal. Already playing at <Picture 1>. Last pulse near 00:07.5, then decay, so the music layer is explicit silence as the image settles on <Picture 2> from 00:08.5 to 00:08.6. The beat does not drive picture changes.
```

### L2VA

`<Picture 1>` = `frames\seg_01_last.jpg` (last frame). The opening is already that frame.

```text
subject_definitions: <Subject 1> is the text card on <Picture 1>. <Subject 2> is the dim interior and seated figure on <Picture 1>. <Picture 1> is the sole authority for type, colors, costume, and layout. Vertical 9:16. Duration 8.60 seconds.

visual_anchor: <Picture 1> is the last frame and also the opening frame. The clip does not approach this card from another setup. It is already this card.

integrated_multimodal_description: Reverse path is a hold, not a build. The ending plate is the starting plate. [Shot 1] At the open the frame already matches <Picture 1>: the red header, all seven bars, and the red footer are already on screen, and the seated figure is already still. No diegetic sound. Nothing is erased or added on the way to the end. [00:07.5] The non-diegetic bed gives its last pulse and decays; the frame stays on <Picture 1>. [00:08.5] The music layer is silent and the frame is still <Picture 1> through the end.

camera_direction: Locked-off, square to the card, matching <Picture 1> from the first frame. None amplitude, none speed, motivated by reading time. No zoom, push, pull, pan, tilt, roll, orbit, truck, handheld, parallax, drift, or Ken Burns. Do not start wide and push in to find the card.

editing: One unbroken take. No opening fade-in, no line-by-line build toward <Picture 1>, no cuts, no flash, no kinetic type. The end frame is <Picture 1> because the start frame was already <Picture 1>.

performance: No performance. The figure on <Picture 1> does not acquire a new expression before the end. No lip-sync.

body_mechanics: No wind-up and no travel. The pose at the end is the pose at the start.

costume_hair_physics: No cloth, hair, or type motion. Nothing needs to settle.

negative_constraints: Do not open on a blank room, a title-only header, or a partial list. Do not animate toward <Picture 1>. No translation, no extra people, no watermark, no ken burns, no zoom, no pan, no tilt, no roll, no drift, no cut, no face motion. The beat must not move the picture.

overall_soundscape: No diegetic ambience, no voice, no foley. The picture is silent for all 8.60 seconds.

non_diegetic_music: A bass-forward electronic beat at a fixed 168 BPM, dry kick every 0.357 seconds, almost no bright cymbals, no intelligible vocal. Already playing when the card is first seen. Last pulse near 00:07.5, then decay. From 00:08.5 to 00:08.6, while the frame remains <Picture 1>, the music layer is explicit silence. The beat does not drive picture changes.
```

終端状態（この1本で完結。次のセグメントはない）。完成したカードが全面のまま、着座人物は動かず、音楽層は無音。仮に次段を切るなら、この保持から開く。

## Checklist

### 証拠
- ffprobe 済み。8.601 秒、1080×1920、60 fps、音声あり。
- 疎グリッド 2 枚、密グリッド 3 枚、4 fps 密フレーム、先頭と末尾の原寸、文字帯の切り出しを確認した。0.00 / 2.00 / 4.00 / 6.00 / 8.20 秒の生フレーム差分は移動 0。大きな差は文字縁だけ。
- スペクトル、0.5 秒 RMS、onset を照合。固定 168 BPM（間隔の std/mean＝0.022、キック格子あり）。自由散板ではない。
- RMS の山（最大は 4.0 秒）に画面の原因はない。強 onset 7 個もすべて画面変化なし。切る先がないので、照合結果は「楽曲のみ」で閉じる。
- scene 検出は 0。火光などの偽カットはない。ショット数は 1。
- 画外から入る手や袖はない。着座人物は静止写真の一部。
- バーの透過、手元の器の種類、極薄のハミングは推測に落とした。

### 内容とカメラ
- 視覚イベントは「完成カードを保持」だけ。隣接動作の残留運動量は、動きが無いので発生しない。
- 映像タイプは A。カメラ機構は全編ゼロ移動。B の BURST は書いていない。C のカメラ位置名も書いていない。
- カメラ割り（ショットサイズ・位置・動き・動機）は分析の表に 1 行。
- 液体、髪、衣装の状態変化はない。
- フリーズフレームのギャグはなし。N-beat はなし。

### 形式
- Ref2VA は六段。T2VA / I2VA / FL2VA / L2VA は 14 欄の順。自作フィールドは置いていない。
- [Shot 1] に時刻はない。その後は 00:07.5（または 00:07.52）と 00:08.5 のみで、どちらも音の減衰。Ref2VA は小数第二位。
- 同期音は置かず、環境音は無音、音楽は non_diegetic だけ。固定拍なので BPM を書いた。
- 各プロンプトの地の文は英語。画面上の日本語は原文のまま。発話タグは使っていない。
- I2VA は冒頭のアンカー文と visual_anchor があり、環境と照明の欄は省いた。
- 長さ 8.60 秒。ffprobe 8.601 秒との差は 0.001 秒。
- 曲名、歌詞、商標は書いていない。

### 複数画像と分割
- ユーザー供給の参考画像はなし。I2VA 以降は先頭または末尾フレームがアンカーで、外観の再記述はしていない。
- セグメントは 1 本、8.60 秒。段内時計は 00:00 から。音楽の再開はない。末尾に終端状態を書いた。次セグメントはない。

### 差し替え
- キャラクター差し替えはなし。対照表は不要。
