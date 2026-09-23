# ふたなりレイ脱出 引き継ぎプロンプト

この文を Cursor でも Grok でも、そのまま最初の指示として貼る。チャット履歴は正本にしない。正本は下のファイルだけ。両方のツールは同じブランチの同じファイルを編集する。病棟出口・霞東とは別チャット。

## 役割

`futanari-rei-escape` の既存カットだけを直す。新しい話、新しい敵、投稿、トレードはしない。生成ボタンは人間が押す。こちらは台本・つなぎ・テストを合わせる。

## 正本（ここだけを編集する）

- リポジトリ: `fireworker011/Research`
- ブランチ: `cursor/futanari-rei-escape-34e4`
- PR: https://github.com/fireworker011/Research/pull/146
- Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/futanari-rei-escape-34e4/minimax_h3_rei_escape_bot.ipynb
- 生成入力: `minimaxh3/episodes/futanari-rei-escape/episode.json`
- カット単位の原稿: `stories/futanari-rei-escape/`。生成に使う文と食い違ったら、`episode.json` とテストを正にする
- エンジン: `colab/h3_episode.py` を直したら、同じ内容を `minimaxh3/h3_episode.py` にコピーする。片方だけ直さない
- Colab 入口: `colab/h3_episode_colab_main.py` と `minimaxh3/h3_episode_colab_main.py` も同様に揃える
- ノートのフォーム: `colab/_write_rei_escape_nb.py` を直し、`python3 colab/_write_rei_escape_nb.py` で `minimax_h3_rei_escape_bot.ipynb` と `minimaxh3/minimax_h3_rei_escape_bot.ipynb` を再生成する。ipynb を手で直さない
- テスト: `python3 -m pytest colab/test_h3_episode.py -q`
- このファイル: `minimaxh3/episodes/futanari-rei-escape/HANDOFF.md`。仕様が変わったら、ここを同じコミットで更新する

触らない: `minimax_h3_episode_bot.ipynb`、`hospital-exit-adult`、`kasumi-late-desk`、`kasumi-late-desk-adult`、inbox、投稿。この話は共有ノートのドロップダウンに足していない。

## プロンプトの書き方

- 英語の動作文。日本語は「」のセリフだけ
- 体位の名前は書かない。誰がどこへ動くかを書く。`doggy` `missionary` `cowgirl` `blowjob` `fellatio` をプロンプト本文に書かない
- 否定で消したいものを描かせない。`blood` `zombie` `corpse` `feces` `shit` `garment` は書かない
- 足が切れる参照があっても、画面は全身、両足まで入れる
- 数字は台本とテストに既にあるものだけ使う。尺や売上を新しく作らない

## 見た目（毎回）

レイ: 21歳、茶髪ロングストレート、スレンダー、くびれ、Cカップ、ふたなり、絶対全裸、素足。24cm は自分の肌の竿で、射精後も股間に残る。普段の顔は口を閉じ、舌は口の中。舌を出すのは、そのカットの動作がじゅぼの快感かイキ顔と書いたときだけ。主人公の名前はレイだけ。

敵1: レイの2倍。薄ミント灰の湿った肉。円口はひょっとこ状に窄めた唇環。大口の漏斗にしない。人間の顔・手・唇を出さない。円口の行為は mystic のみ。口 LoRA は載せない。

蛾女: 上半身はレイと同じ背丈の裸体の女性。下半身は節腹、多脚、翅、尾。尾の先端の円口。森は出さない。場所は肉壁。

サキュバス: 黒髪、赤い目、黒い角、顔の紋、チョーカー、破れた翼、長い尾、爪。全裸、無毛。翼・角・チョーカー・紋・爪は残す。

壁は肉だけ。`world.bare_set` は true。看板・テレビ・陶器の便器は出さない。トイレは肉が洋式の形。脱糞は書かない。トイレのあと肌に糞を塗らない（`DIRTY-STATE` は今の生成では付かない）。

## つなぎ（確認済み）

Colab の「前の最終フレームから続ける」は `connect=chain`。

- 最初の `01-open-stroke` は T2V
- 新しい相手の入りは台本が `connect: t2v` で固定。チェーンを選んでも T2V のまま。対象は `04-enemy1`、`08-toilet`、`12-moth`、`16-succ`
- 同じ相手の次の行為は I2V。例: `05-enemy1-maw`、`17-from-rei`、`20-fours-in`、`21-orgasm`
- 相手が消える走りは I2V のまま、最初の2秒でフェードする。`06-fade-run-b` は beast、`22-succ-fade` は succubus
- 「カット」を選ぶと全部 T2V
- シーン終わり用の別ドロップダウンは無い

## フォームの既定（迷ったらそのまま）

- 合間おな: しない。`03` `07` `11` `15` は出ない。立ちか仰向けを選ぶと、その4本が足される
- トイレ: 着座おな射精（`09-ta`）。小便は着座。触手は肉壁の円口が 24cm を根元まで吞む（`09-tc`、mystic）
- 敵1: 受け入れる＝立ち円口（`05-enemy1-maw`）。誘う＝その場で仰向け、笑顔で膝を開く（`05-enemy1-invite`）。回避＝その行為を飛ばしてフェードから走り。回避の走りに射精の文は書かない
- 蛾女: 尾端の第二口（`13-tail`）。両方立ち止まる。上の口を選ぶと唇と舌（`13-mouth`、blowjob LoRA）
- 誰から: レイから（`17-from-rei`）。サキュバスから（`17-from-her`）。この文は 17 だけ。18 以降のキス・口・挿入・絶頂には付けない
- キス: しないが既定。するときは顔のキス。フェラではない
- 口: しないが既定。サキュバスがフェラ、またはレイがクンニ。体位のカットにキスや口を戻さない
- 挿入: 四つん這い後ろからが既定（`20-fours-in` のあと `20-fours-out`）。壁に手は掌を壁、足は固定、竿は膣の中。跨がりは沈めて上げ下ろし、レイは仰向け。仰向けは相手が仰向けで膝を開く
- 最後は完了。失敗カードは無い。任務は「異形の体内から脱出」
- 4番の格闘 LoRA は既定オフ。この `episode.json` に `combat_on` は無い。戦い文は足さない
- 走りだけ `loco=run`。行為・トイレ・蛾・挿入は `loco=planted`。背景はスクロールしない

## メモリ

成功したカットの前に VRAM は下ろさない。メモリ不足で失敗したときだけ下ろし、次の短い尺を試す。毎回解放のスイッチは無い。

## 作業の終わり

1. テストが通る
2. `colab/` と `minimaxh3/` の対応ファイルが同じ
3. このブランチへコミットして push
4. PR #146 の説明を、変わった事実だけ直す
5. 人間へレイ脱出の Colab リンクを返す。再生成は FRESH をオン。raw が既にあるカットは、FRESH がオフだと作り直さない
