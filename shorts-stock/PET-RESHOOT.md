# ペット #03–#10 撮り直しプロンプト（Grok Imagine）

チャンネル: ペットと暮らす小さな物語（@pet_story_select）。見守りカメラの Shorts、猫だけ。
元: `shorts-stock/2026-10-12/pet/03..10` の SCRIPT.md / STYLE.md / VOICE.md と `shorts-stock/PROMPT-RULES.md`。

Imagine は始めない。ナオミチが手で1行ずつ貼る。投稿もしない。

## 直すこと

8本とも、同じグレー猫×ソファと白猫×ラグのクリップを使い回していた。台本とも合っていなかった。
ここでは1本ごとに猫・部屋・時間帯・カメラの高さを変え、STYLE.md の C（カメラ）と P（色）に合わせた。

## 守ったこと

- 1行の英語を、そのまま Imagine に貼る。縦 9:16、約5秒。
- 全行に固定カメラ、見守りカメラの画、時刻表示なしを入れた。
- 人、人の顔、人の手、文字、ロゴ、音楽、せりふは出さない。
- 1ショットに動作は1つ。カメラは動かない。
- 毛色は声に合わせた。奇数はグレー系（声が「グレー」）、偶数は白系（声が「白い子」）。品種、柄、毛の長さ、目の色は1本ずつ変えた。
- #03 と #04 は台本のオチがラグからソファなので、ラグとソファは残した。そのかわり、部屋、ソファ、ラグ、品種、時間帯、カメラの高さを #01・#02 と違うものにした。
- 生成は5秒。台本のショットが2秒か4秒のときは、`finish.sh` が「使う秒」だけを頭から使う。
- 各本は、その本の1ショット目で出た猫の静止画を2ショット目と3ショット目の参照画像に添付する。同じ猫に見えるようにするため。

## 一覧（どの2本も、猫と部屋の組が重ならない）

| 本 | 猫 | 部屋 | 時間と光 | カメラ | STYLE |
| --- | --- | --- | --- | --- | --- |
| #03 | グレーのサバトラ、アメリカンショートヘア | 狭いワンルーム。丸い編みラグ、チャコールの革の2人掛け | 深夜。赤外線の白黒 | 天井から真下、あとで高い隅 | C3 俯瞰 / P6 モノトーン |
| #04 | 白の長毛ターキッシュアンゴラ、オッドアイ | 屋根裏のロフト。白木の床、丸いジュートラグ、木枠のフトンソファ | 昼前。やわらかい外光 | 床の高さ | C2 床目線 / P2 白×木目 |
| #05 | ロシアンブルー、細身、緑の目 | 和室。畳と障子、ちゃぶ台 | 夕方。暖色の行灯 | 鴨居の高さから部屋全体 | C6 引き / P1 グレー×暖色 |
| #06 | 白のペルシャ、長毛、青い目 | キッチンの床。白いタイル、冷蔵庫の下 | 曇りの午後。色を落とす | 低い棚の上から寄り | C5 寄り / P6 モノトーン |
| #07 | ブリティッシュショートヘアのブルー、ずんぐり、銅色の目 | 書斎。机、本棚、デスクライト | 深夜。デスクライトだけ | 高い隅から部屋全体 | C6 引き / P5 夜の間接照明 |
| #08 | 白のジャパニーズボブテイル、短いポンポンの尾、金の目 | 玄関。たたき、靴箱、すりガラスの戸 | 夜明け。青白い光 | 天井から俯瞰 | C3 俯瞰 / P4 朝の青白 |
| #09 | シルバーグレーの長毛ノルウェージャンフォレストキャット | 寝室の床。ベッドの脚、ベッド下の暖色LED | 夜。足元灯だけ | 床の高さ | C2 床目線 / P5 夜の間接照明 |
| #10 | 白のデボンレックス、大きな耳、ウェーブの短毛 | サンルームの窓辺。籐の椅子、観葉植物 | 夕方。窓の逆光で縁が光る | 窓台の高さ、横から | C4 窓辺の逆光 / P1 グレー×暖色 |

#01（グレー猫×ソファ）と #02（白猫×ラグ）の画は、どの本にも使っていない。#03 と #04 も、品種、部屋、光、カメラの高さが #01・#02 と違う。

---

## #03 ラグの猫が、ソファにいた（12秒）

STYLE `pet:C3-P6-T3-F6-H1-M6-B2-L1-A1`：見守りカメラ俯瞰、モノトーン。

- `pet-03-1.mp4`　使う秒: 0–2（2秒）

```text
Vertical 9:16, 5 seconds, fixed ceiling-mounted security camera looking straight down, night-vision infrared black-and-white footage with slight grain and soft lens vignette, a small dark studio apartment floor, one adult gray mackerel-tabby American Shorthair cat with dark stripes and green eyes sits still on a round braided rug, the cat only sits and breathes, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-03-2.mp4`　使う秒: 2–7（5秒）

```text
Vertical 9:16, 5 seconds, fixed ceiling-mounted security camera looking straight down, night-vision infrared black-and-white footage with slight grain and soft lens vignette, the same small dark studio apartment, the same gray mackerel-tabby American Shorthair cat stands on the round braided rug and walks off the edge of the frame, leaving the empty rug, camera completely locked and does not follow the cat, one soft paw step then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-03-3.mp4`　使う秒: 7–12（5秒）

```text
Vertical 9:16, 5 seconds, a second fixed security camera mounted high in a corner angled down at a charcoal leather two-seat loveseat, night-vision infrared black-and-white footage with slight grain, the same small dark studio apartment, the same gray mackerel-tabby American Shorthair cat curls into a tight ball on the loveseat cushion and stays still, large in the center of the frame, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

## #04 ラグの白い猫が、ソファにいた（12秒）

STYLE `pet:C2-P2-T1-F1-H6-M2-B2-L1-A2`：床目線ローアングル、白×木目。

- `pet-04-1.mp4`　使う秒: 0–2（2秒）

```text
Vertical 9:16, 5 seconds, fixed pet camera placed on the floor at cat eye level, home security-cam look with slight wide-angle distortion, late-morning soft daylight in a bright attic loft with pale oak floorboards and white walls, one adult white long-haired Turkish Angora cat with one blue eye and one amber eye sits on a round natural jute rug, the cat only sits still, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-04-2.mp4`　使う秒: 2–7（5秒）

```text
Vertical 9:16, 5 seconds, fixed pet camera on the floor at cat eye level, home security-cam look with slight wide-angle distortion, the same bright attic loft with pale oak floorboards in late-morning daylight, the same white long-haired odd-eyed Turkish Angora cat steps off the round jute rug and walks out of the frame, leaving the empty rug, camera completely locked and does not follow, one soft paw step then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-04-3.mp4`　使う秒: 7–12（5秒）

```text
Vertical 9:16, 5 seconds, a second fixed pet camera low on the floor facing a wooden-frame futon sofa with a cream cushion, home security-cam look, the same bright attic loft in late-morning daylight with white walls and oak wood, the same white long-haired odd-eyed Turkish Angora cat curls into a ball on the futon cushion and stays still, large in the center of the frame, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

## #05 見守りカメラに、猫が触った（10秒）

STYLE `pet:C6-P1-T2-F3-H3-M4-B2-L1-A1`：引きの部屋全体、グレー×暖色。

- `pet-05-1.mp4`　使う秒: 0–2（2秒）

```text
Vertical 9:16, 5 seconds, fixed security camera mounted high on the wall showing the whole room, wide-angle pet-cam look, early evening in a Japanese tatami room with shoji screens and a low wooden chabudai table lit by a warm paper floor lamp, one slim adult Russian Blue cat with short silver-blue coat and green eyes sits on the tatami and turns its head to look up at the camera, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-05-2.mp4`　使う秒: 2–6（4秒）

```text
Vertical 9:16, 5 seconds, fixed high wall security camera showing the whole tatami room, wide-angle pet-cam look, warm paper lamp light in the early evening with shoji screens, the same slim Russian Blue cat with green eyes, already looking at the camera, takes one step across the tatami toward the camera, camera completely locked and does not follow, one soft paw step then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-05-3.mp4`　使う秒: 6–10（4秒）

```text
Vertical 9:16, 5 seconds, fixed security camera sitting on a low shelf in the tatami room, wide-angle pet-cam look with the warm paper lamp glowing behind, the same slim Russian Blue cat with green eyes is right in front of the lens and taps the lens once with one front paw, the paw pad briefly fills the foreground, camera completely locked with no pan, tilt, zoom or follow, one soft tap then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

## #06 見守りカメラに、白い猫が触った（10秒）

STYLE `pet:C5-P6-T5-F3-H6-M1-B1-L1-A2`：寄りのクローズアップ、モノトーン、ワンカット長回し。3本は同じ位置のカメラでつなぐ。

- `pet-06-1.mp4`　使う秒: 0–2（2秒）

```text
Vertical 9:16, 5 seconds, close-up from a fixed pet camera sitting on a low kitchen shelf, desaturated near-monochrome security-cam footage with soft grain, overcast afternoon light on white floor tiles beside the base of a fridge, one adult white long-haired Persian cat with a flat face and blue eyes fills the frame and lifts its gaze to the lens, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-06-2.mp4`　使う秒: 2–6（4秒）

```text
Vertical 9:16, 5 seconds, close-up from the same fixed pet camera on a low kitchen shelf, desaturated near-monochrome security-cam footage with soft grain, overcast afternoon light on white floor tiles, the same white long-haired flat-faced Persian cat with blue eyes, already looking at the lens, takes one step closer so its face and fluffy chest grow larger in frame, camera completely locked and does not follow, one soft paw step then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-06-3.mp4`　使う秒: 6–10（4秒）

```text
Vertical 9:16, 5 seconds, extreme close-up from the same fixed pet camera on a low kitchen shelf, desaturated near-monochrome security-cam footage, overcast afternoon light, the same white long-haired flat-faced Persian cat with blue eyes reaches up and touches the lens once with one fluffy front paw, the soft pink paw pad presses close to the glass, camera completely locked with no pan, tilt, zoom or follow, one soft tap then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

## #07 見守りカメラに、猫が1回鳴いた（10秒）

STYLE `pet:C6-P5-T1-F1-H5-M3-B6-L1-A1`：引きの部屋全体、夜の間接照明。

- `pet-07-1.mp4`　使う秒: 0–2（2秒）

```text
Vertical 9:16, 5 seconds, fixed security camera mounted high in the corner of a home study showing the whole room, wide-angle pet-cam look, late night lit only by an amber desk lamp, a wooden desk and tall bookshelves with plain spines, one stocky adult blue British Shorthair cat with a dense plush gray coat, round cheeks and copper eyes sits on the wooden floor and looks up at the camera, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-07-2.mp4`　使う秒: 2–6（4秒）

```text
Vertical 9:16, 5 seconds, fixed high corner security camera showing the whole home study, wide-angle pet-cam look, late night lit only by an amber desk lamp, the same stocky blue British Shorthair cat with copper eyes, already looking at the camera, takes one step across the wooden floor toward the camera, camera completely locked and does not follow, one soft paw step then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-07-3.mp4`　使う秒: 6–10（4秒）

```text
Vertical 9:16, 5 seconds, fixed security camera on top of the bookshelf in the home study, wide-angle pet-cam look, late night lit only by an amber desk lamp, the same stocky blue British Shorthair cat with copper eyes stands closer below the camera, looks up, opens its mouth and meows once, then stays still, camera completely locked with no pan, tilt, zoom or follow, one short meow then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

## #08 見守りカメラに、白い猫が1回鳴いた（10秒）

STYLE `pet:C3-P4-T3-F5-H2-M3-B4-L1-A2`：見守りカメラ俯瞰、朝の青白。

- `pet-08-1.mp4`　使う秒: 0–2（2秒）

```text
Vertical 9:16, 5 seconds, fixed ceiling security camera looking down on a Japanese entryway genkan with a stone floor step, a wooden shoe cabinet and a frosted glass door, cool blue-white dawn light, security-cam look with slight fisheye, one adult white Japanese Bobtail cat with a short pom-pom tail and gold eyes sits on the wooden step and tilts its head up to look at the camera, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no shoes in use, no text, no timestamp overlay, no logo, no music
```

- `pet-08-2.mp4`　使う秒: 2–6（4秒）

```text
Vertical 9:16, 5 seconds, fixed ceiling security camera looking down on the same Japanese genkan entryway, cool blue-white dawn light through the frosted glass door, security-cam look with slight fisheye, the same white Japanese Bobtail cat with a pom-pom tail and gold eyes, already looking up, takes one step toward the spot below the camera, camera completely locked and does not follow, one soft paw step then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-08-3.mp4`　使う秒: 6–10（4秒）

```text
Vertical 9:16, 5 seconds, fixed security camera high above the shoe cabinet looking steeply down into the genkan, cool blue-white dawn light, security-cam look with slight fisheye, the same white Japanese Bobtail cat with gold eyes sits directly below, looks straight up, meows once and then stays still, large in the center of the frame, camera completely locked with no pan, tilt, zoom or follow, one short meow then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

## #09 見守りカメラに、猫が1歩近づいた（10秒）

STYLE `pet:C2-P5-T4-F5-H3-M2-B1-L1-A1`：床目線ローアングル、夜の間接照明。

- `pet-09-1.mp4`　使う秒: 0–2（2秒）

```text
Vertical 9:16, 5 seconds, fixed pet camera placed on a bedroom floor at cat eye level, security-cam look with slight noise, night lit only by a warm LED strip under the bed frame, wooden bed legs and a soft bedside rug in the background, one adult silver-gray long-haired Norwegian Forest Cat with a thick ruff and tufted ears lies on the floor and raises its head to look at the camera, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-09-2.mp4`　使う秒: 2–6（4秒）

```text
Vertical 9:16, 5 seconds, fixed pet camera on the bedroom floor at cat eye level, security-cam look with slight noise, night lit only by the warm under-bed LED strip, the same silver-gray long-haired Norwegian Forest Cat, already looking at the camera, takes one step toward the lens, camera completely locked and does not follow, one soft paw step then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-09-3.mp4`　使う秒: 6–10（4秒）

```text
Vertical 9:16, 5 seconds, fixed pet camera on the bedroom floor at cat eye level, security-cam look with slight noise, night lit only by the warm under-bed LED strip, the same silver-gray long-haired Norwegian Forest Cat stands close to the lens, plants one front paw and stops completely still, its fluffy face large in the center of the frame, camera completely locked with no pan, tilt, zoom or follow, one soft paw set-down then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

## #10 見守りカメラに、白い猫が1歩近づいた（10秒）

STYLE `pet:C4-P1-T1-F3-H1-M2-B4-L1-A2`：窓辺の逆光、グレー×暖色。

- `pet-10-1.mp4`　使う秒: 0–2（2秒）

```text
Vertical 9:16, 5 seconds, fixed pet camera at windowsill height facing a sunroom window, home security-cam look, late-afternoon golden backlight with the outside softly blown out, a rattan chair and a potted plant on gray stone tiles, one adult white Devon Rex cat with huge ears, a slim body and short wavy coat glowing with a rim of warm light sits by the window and turns to look at the camera, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-10-2.mp4`　使う秒: 2–6（4秒）

```text
Vertical 9:16, 5 seconds, fixed pet camera at windowsill height in the same sunroom, home security-cam look, late-afternoon golden backlight from the window behind the cat, the same white Devon Rex cat with huge ears and a rim-lit wavy coat, already looking at the camera, takes one step away from the window toward the lens, camera completely locked and does not follow, one soft paw step then room tone, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

- `pet-10-3.mp4`　使う秒: 6–10（4秒）

```text
Vertical 9:16, 5 seconds, fixed pet camera at windowsill height in the same sunroom, home security-cam look, warm golden backlight making a bright halo around the ears, the same white Devon Rex cat stands close to the lens and stops completely still, its large-eared silhouette large in the center of the frame with the empty glowing window behind, camera completely locked with no pan, tilt, zoom or follow, quiet room tone only, no humans, no faces, no hands, no text, no timestamp overlay, no logo, no music
```

## 残したこと

- 各本の `IMAGINE.md` と `../REFS.md` は書き換えていない。この撮り直しで使う猫は REF-GRAY と REF-WHITE ではない。
- `PROMPT-RULES.md` は「`Duration:` をショットの長さと一致」と言う。この頼みは約5秒の1行なので、5秒で生成し、「使う秒」で切る形にした。
