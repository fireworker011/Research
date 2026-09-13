# エピソード一発（MiniMax H3 → 完成動画）

`episode.json` 1つとスチール数枚を置くと、Colab の Run all 一発で
**全ビート生成 → HUD 合成 → タイトル／免責エンドカード → 音声クロスフェード連結** まで終わり、
Drive `minimax-h3-comfyui/episodes/<slug>/final/<slug>-<日時>.mp4`（と `latest.mp4`）が出る。

ネタを変えるときは `_template/` を複製して `episode.json` とスチールを差し替えるだけ。コードは触らない。

| 場所 | 中身 |
|---|---|
| `minimaxh3/episodes/<slug>/episode.json` | 唯一の入力（世界観・キャスト・小道具・ビート・台詞・HUD 状態・免責・失敗カード） |
| `minimaxh3/episodes/<slug>/stills/*.jpg` | クリーンな先頭フレーム。HUD を焼き込まない。1280×720 でよい（1024×576 に自動で正規化） |
| `minimaxh3/episodes/bandai-district/` | 9ビート・92秒の初回版（アクション調）。raw は Drive に残っている |
| `minimaxh3/episodes/bandai-district-short/` | 25秒・ミッション失敗で落ちる版。初回版の raw を `reuse` し、新しく描くのは理容室 1 本 |
| `minimaxh3/h3_episode.py` | スキーマ検査・プロンプト生成と検査・ステージング・レンダ・reuse／ui ビート・HUD・連結・CLI |
| `minimaxh3/h3_hud.py` | HUD／字幕／メニュー／カード描画と ffmpeg（compose / card / stitch / frame） |
| `minimaxh3/h3_episode_colab_main.py` | Colab のヘッドレス入口（env で slug・preset・fresh） |
| `minimax_h3_episode_bot.ipynb` | ワンクリック用ノート。コードセル1本。`colab/_write_episode_nb.py` で再生成 |
| `minimaxh3/grokbot/run_episode.py` | colab CLI からの一発（Automation ではない） |
| `colab/test_h3_episode.py` | スキーマ／プロンプト／LoRA チェーン／OOM／HUD／連結／隔離の回帰テスト |

## 一発の実行

**スマホ／ブラウザ**: [minimax_h3_episode_bot.ipynb](../../minimax_h3_episode_bot.ipynb) を Colab で開き、`EPISODE` に slug、`PRESET` を選んで Run all。
GPU は A100（High-RAM）。終わるとランタイムを自分で手放す。成功時は `DONE` と `episode exit 0` のあと「成功。」と出る。ランタイム切断は予定どおり。IPython の赤い `SystemExit: 0` は出さない。

**PC（colab CLI）**:

```bash
python minimaxh3/grokbot/run_episode.py --episode bandai-district-short      # 25秒・失敗落ち版（理容室 1 本だけ描く）
python minimaxh3/grokbot/run_episode.py --episode bandai-district            # 92秒版 全部
python minimaxh3/grokbot/run_episode.py --episode bandai-district --fresh    # raw を捨てて作り直し
python minimaxh3/grokbot/run_episode.py --episode bandai-district --dry-run  # コマンド確認だけ
```

**GPU なしで確認**（この順で使う）:

```bash
cd minimaxh3
python h3_episode.py check   episodes/bandai-district-short           # スキーマ＋プロンプト検査＋フォント＋ffmpeg＋各ビートの窓と予定尺
python h3_episode.py prompts episodes/bandai-district-short           # logs/<beat>.prompt.txt を書く
python h3_episode.py stills  episodes/bandai-district-short --out /tmp/ep/bandai-district-short   # スチール保持の予告（trim は無視、HUD・カードは本番と同じ）
python h3_episode.py dry-run episodes/bandai-district-short --out /tmp/ep/bandai-district-short   # 合成クリップで全パイプライン
python h3_episode.py finish  /path/to/episodes/<slug>                 # raw/*.mp4 があるとき HUD＋連結だけやり直す（reuse 元があれば raw/ にコピーしてから）
```

`--out` を付けるとリポジトリのフォルダを汚さない。付けないと `episodes/<slug>/` 直下に raw/hud/final ができる（git に入れない）。
`reuse` は `--out` の**親フォルダ**にある兄弟 `episodes/<元slug>/raw/` を探すので、`--out /tmp/ep/<slug>` のように slug 名で終わらせる。

## 本家と初回版を並べて分かったこと（2026-09-12）

参照元（約96秒）と初回の番台ディストリクト（92秒）をフレーム単位で比べた結果。**借りるのは見せ方の文法だけ**、映像・人物・小道具は一切コピーしない。

| 項目 | 参照元 | 初回版 | 直したもの |
|---|---|---|---|
| カット | 約25カット、平均 3〜4秒 | 9カット × 10秒 | `beat.trim` で 10秒素材から 3〜6秒の窓だけ使う |
| 小道具 | 各ショットに 1 つ | 全プロンプトに全小道具を注入 → 暖簾（4.5秒）・自転車（6.5秒）・理容室（1秒）に軽トラが出現 | `beat.props` でビートごとに指定。全部入れる経路は削除 |
| 場所 | 1ショット 1場所 | 理容室の室内が 1秒で商店街に変わる | 全プロンプトに「一続きのワンテイク・同じ場所・新しい物は入らない」の肯定文を足す |
| トーン | 映像は日常のまま、字幕だけが犯罪ゲーム | 後半で爆発・アッパー・ラグドールを映像でやろうとして崩壊 | `tone: "mundane"`（爆発・ジャンプ等の語は否定形でも禁止、physics 禁止、顔ショット 2 本まで） |
| 落ち | ミッション失敗 | ミッション完了 | `cards.fail`（最後のビートは complete 不可） |
| 会話 | HUD を消して字幕だけ | HUD 出しっぱなし | `hud.visible: false` ＋ `speech[].text` の字幕 |
| ミッション行 | 目的語だけ赤 | 全部白 | `hud.mission_keyword` |
| 小ネタ | 停止画面のアイテム一覧 | なし | `source: "ui"` ビート（前のビートを止めてメニューを重ねる。GPU 不要） |
| 冒頭 | いきなり本編 | タイトルカード | `cards.title: false` |
| 顔 | 同一人物 | スチールごとに別人（03/07/08） | 使える raw を `reuse` して顔ショットの再生成を最小化 |

短縮版はこの表をそのまま実装したもの。暖簾 3.0秒 → 自転車 5.0秒 → 理容室（字幕のみ・完了）6.0秒 → 道具メニュー 2.2秒 → 軽トラ乗車 4.8秒 → **ミッション失敗「薪を積みすぎて軽トラが動かなかった」** 2.8秒 → 免責 3.0秒 ≈ 24.7秒。

## 途中で止まったら

`raw/<beat>.mp4` が残っているビートは飛ばして続きから描く。壊れた本だけ消して再実行、または `FRESH`（`--fresh`）で全部作り直し。
進行は `status.json`、各本のプロンプトは `logs/<beat>.prompt.txt`。

## episode.json の決まり

- 英語で書く。日本語は台詞の中身だけ（`speech[].line`、かな限定、`「」` は自動で付く）。HUD の文言（`hud.mission` など）は日本語でよい（画面に後載せするだけで H3 には渡さない）
- 1ビート = 1場所 1動作 10秒。`clip_seconds` は 4〜10。15秒は使わない（OOM でキャンバスが縮む）
- `source`: `still`（クリーンな先頭フレーム）／`chain`（前の本の**切った位置**のコマから続ける。先頭の本では使えない）／`t2v`（先頭フレームなし）／`ui`（前の本を止めてメニューを重ねる。`seconds` 1.5〜5、`menu {title, items 2〜8, selected}`。GPU もプロンプトも無し。先頭と連続は不可）
- `tone`: `mundane`（映像は日常のまま。`violence` は `none`、`physics` 禁止、action/camera/place に爆発・ジャンプ・格闘・追跡などの語を書くと否定形でも落ちる、`face_visible` は 2 本まで。プロンプトに「平穏な日常の動作」を足す）／`action`（旧来どおり。省略時）
- `props` はビートごとに `beat.props: ["tenugui"]` で指定する。省略すると本文に名前が出た小道具だけ付く。**全小道具を全ビートに入れる経路は無い**（初回版で軽トラが全ショットに出た原因）
- `trim: {"start": 0, "seconds": 4.0}` で 10秒素材のうち使う窓を決める（1.5秒以上、`clip_seconds` 内）。生成は 10秒のまま、切るのは合成時。`chain` は前の本の窓の終わりから続く
- `reuse: "bandai-district/01-exit-noren"` で兄弟エピソードの `raw/` を使う。元が Drive に無ければ `still` から描く（無ければ止まる）。`check` が on disk / missing → render を表示
- 台詞は `face_visible: true` の本だけ、1本2行まで。`speech[].text` は画面の字幕（漢字可、30字まで。省略時はかなの `line`）、`at` / `until` 秒で出す時間を指定できる（省略時は窓を等分）。`hud.subtitles: false` で字幕を止める
- `hud.visible: false` はカットシーン（バー・ミニマップ・ミッション行を消して字幕だけ。`complete` のフラッシュは出る）。`hud.mission_keyword` はミッション行の中の目的語で、アクセント色になる
- `cards.fail: {"text": "ミッション失敗", "reason": "…30字まで", "seconds": 2.8, "image": "last-frame"}` を入れると最後のビートの切った位置で止めて失敗カードを出す（`image` はパスでも可）。最後のビートに `complete: true` は置けない。`cards.title: false` でコールドオープン。`title_seconds` / `end_seconds` は 1.5〜6
- `cast[].age` は成人（20以上）。子供は画面にも文にも入れない（自動で「Adults only in frame」を付け、未成年語は検査で落ちる）
- `violence: "game"` ＋ ビートの `physics: true` で「大人がラグドールで飛ぶ・血なし・怪我なし」の文を自動で足す。流血・ゴア語は正の文で書くと落ちる
- `homage.never` に、参照元の固有要素（物・人名・小道具）を並べる。プロンプトに出たら落ちる。ブランド／IP 名（格ゲー・オープンワールドの実名、Pollo、Seedance）と「HUD・ミニマップ・字幕・透かし」を H3 に描かせる語も落ちる。`lip-synced` などの英語メタも落ちる（H3 が読み上げる）
- `cards.disclaimer` は必須。エンドカードに「架空のゲームのコンセプト映像」を出す
- `canvas`: `16:9`（1024×576）か `9:16`（576×1024）。出力は `stitch.output_height` 720 か 1080

## レンダの決まり

- LoRA プリセット: `daily` = Larry v4 1.0 + シネマ DY 0.65 / 8step（トリガー `DY` を先頭に付ける）、`preview` = LightX2V 4step + シネマ 0.5、`fast` = LightX2V 4step のみ。Larry と LightX2V は同時に積まない。ファイルが無ければ `fallback_preset` に落ちる（`status.json` に記録）
- OOM のときはキャンバスを維持して秒数だけ 10→8→6 に落とす。先頭フレームは外さない
- 音は H3 のまま。連結は xfade + acrossfade 0.35秒 + loudnorm。`transition: "cut"` で直結

## 本番を壊さないための境界

- Drive は `episodes/<slug>/` の下だけに書く。`inbox/queued/running/done/failed/input/output` は触らない。`models/` は読むだけ
- 本番 I2V の `drop_job.py` / `run_i2v.py` / 15分 Automations にエピソードを入れない（裸 jpg はココナラ I2V に拾われ、Imagine 既定文でキャラが消える）
- Imagine 2.0 は呼ばない。`XAI_API_KEY` は不要
- helper は GitHub のブランチから `/content` へ取り、Drive は `episodes/_lib/` にだけキャッシュ。本番ルート直下の同名ファイルは上書きしない
- LoRA スタジオ（`h3_lora_studio.py`、③、STORY）には足さない
- 投稿しない。アフィ URL・収入主張はプロンプトに入れない（検査で落ちる）

## 番台ディストリクト（2 本）

**bandai-district-short（次に回すのはこれ）**: 5ビート ≈ 24.7秒、コールドオープン、`tone: mundane`。暖簾 3.0秒 → 自転車 5.0秒 → 理容室（HUD なし・字幕・完了）6.0秒 → 道具メニュー 2.2秒 → 軽トラ乗車 4.8秒 → ミッション失敗 → 免責。
暖簾・自転車・軽トラは `bandai-district/raw/` の初回テイクを `reuse`（Drive に残っている）。GPU で描くのは理容室 1 本だけ（初回テイクは 1秒で室内が商店街に変わっていたので作り直す。今回は小道具が手ぬぐいだけ＋ワンテイク固定文）。Colab は `EPISODE = "bandai-district-short"`、Grokbot は `minimaxh3/GROKBOT.md` の貼り付け。

**bandai-district（初回版・アクション調）**: 9ビート × 10秒 ＋ タイトル 2.6秒 ＋ エンド 3.2秒 ≈ 92秒。暖簾 → 自転車 → 理容室 → 会話 → 軽トラ → 吹き飛び走行 → 蒸気アッパー → 釜爆発 → 着地。
小道具はビートごとに直し、03/04 はカットシーン、ミッション行に赤字を入れた。`--fresh` で描き直せば前半の軽トラ混入は消えるが、後半の爆発ビートは H3 の得意ではない（`tone: action` のまま残す）。

どちらも借りたのは三人称カメラとミッション字幕の文法、会話で HUD を消す作法、失敗で落とす間だけ。舞台・人物・物語はオリジナル。参照元の要素は `homage.never` で禁止。

## こがね厨房（`kogane-timecard`）

25秒。参照のシュールは「しゃがんだまま脛を引っかけて店主を座らせる」1本だけ借りる。学校・制服・段ボール箱・原クリップは使わない。
クレート 3.0秒 → 足払い（ゲーム物理・血なし）5.0秒 → 厨房（字幕のみ・伝票完了）6.0秒 → 道具メニュー 2.2秒 → 打刻 4.8秒 → ミッション失敗「タイムカードを裏向きに挿した」→ 免責。
爆発・飛び蹴りは書かない。`tone: action` はこの足払いのため。Colab は `EPISODE = "kogane-timecard"`。inbox には置かない。
