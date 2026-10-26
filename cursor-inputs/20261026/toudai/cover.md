# 指示書 2026-10-25-10 灯台町の契約：DLsite表紙の元絵

目的: DLsite用の表紙の元絵（文字なし）を作る。文字入れは箱で後からやる。
順番: 指示書09が終わってから始める（PCのジョブは一度に1つ）。
枚数: 6 seed（2026102501〜2026102506）×1枚＝6枚。
解像度: 1344×1008。Hires.fix ×1.5で2016×1512。
モデル: waiIllustriousSDXL_v170 [f116b0c78f]
設定: 標準（Euler a／Automatic／Steps 28／CFG 7／Hires.fix R-ESRGAN 4x+ Anime6B、steps 15、denoise 0.3、Hires CFG 7／Refiner OFF／Batch 1×1）

## プロンプト
masterpiece, best quality, amazing quality, very aesthetic, absurdres, newest, anime coloring, game cover art, key visual, 7girls, multiple girls, group shot, mature female, adult women, varied heights, standing, looking at viewer, confident expression, gentle smile, fully clothed,
foreground right: 1girl, long black hair, straight hair, dark blue eyes, navy blue high-collar wool coat, brass lighthouse brooch, cowboy shot, hand on own chest,
background group left: silver hair, braided updo, charcoal gray pantsuit, arms crossed; dark brown hair, elegant updo, crimson kimono, obi, holding folding fan; blonde hair, low ponytail, dark green long coat; reddish brown hair, single braid, off-white long robe, holding book; grayish purple hair, low tied hair, brick red work clothes, rolled sleeves, holding hammer; teal hair, short hair, sand-colored diving suit, holding diving helmet,
harbor town, port town, lighthouse on cape, lighthouse beam, stone pavement, gas lamps, sailing ships, wooden pier, sea, dusk, sunset, orange and purple sky, warm light, cinematic lighting, depth of field, wide shot, empty sky upper left, no text

## ネガティブ
child, loli, teen, young girl, aged down, petite, flat chest, school uniform, serafuku, student, nsfw, nude, nipples, underwear, see-through, bad anatomy, bad hands, extra fingers, missing fingers, fused fingers, extra limbs, deformed, bad proportions, cloned face, same face, text, logo, letters, watermark, signature, speech bubble, worst quality, low quality, lowres, jpeg artifacts, blurry, photorealistic, 3d

## 崩れたとき（直しは最大3周）
1周目で6枚とも人数や顔が大きく崩れたら、Regional Prompter（入っていれば）で画面を左右に分け、右に澪、左に6人を割り当てて同じseedでやり直す。入っていなければ、人数を「1girl（澪）＋背景の港町」に減らした版を同じseedで6枚作る。それ以上は工夫しない。

保存先: PC C:\work\toudai-cover\order10\（原寸PNG、params.txt）。露骨さなしの表紙なので、原寸PNGをナオミチの非公開Drive（またはGrok Bot経由で箱 /home/box/doujin/toudai/cover-raw/）へ送ってよい。
Eagle専用タグ: 灯台町の契約, 表紙, DLsite表紙, なし, WAI_v17, seed:<n>
完了条件: 6枚（崩れた場合の作り直し分は別に数える）／2016×1512／裸・下着・幼い見た目・文字がない／params.txtにpromptとseed／Eagle専用に登録。
上限: 直しは最大3周、時間は最大1時間。届いたら止めて C:\work\toudai-cover\order10\handoff.md に「どこまで・何で止まったか・次」を書く。
報告（文字だけ）: 各seedを1行ずつ（何人出たか、澪が右手前か、顔や手の崩れ、左上の空きがあるか）、おすすめseed、所要時間、箱に送ったファイルのパス。
守ること: 全員18歳以上・大人の見た目。公開・出品・送信はしない。
