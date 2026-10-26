# Cursorクラウド指示書 2026-10-26（起動の手順）

作成: 2026-10-26 18:45 JST（Grok Bot executor）。指示書を書いただけで、起動・push・送信はしていない。

## 起動前に1回だけ（入力をリポジトリへ）
Cursorクラウドは /home/box を読めないので、入力ファイルを先に GitHub へ置く。
```
cd /tmp && rm -rf r && gh repo clone fireworker011/Research r && cd r
git checkout -b cursor/briefs-inputs-20261026
mkdir -p cursor-inputs && cp -r /home/box/bots/cursor-briefs/20261026/inputs cursor-inputs/20261026
git add cursor-inputs && git commit -m "Cursor指示書 2026-10-26 の入力ファイル" && git push -u origin cursor/briefs-inputs-20261026
```
（入力の中身: 共通ルール・QC5・台本の型・勝ち型メモ・リサーチ反映の抜き書き、konkatsu-01〜05、pet-03〜05、kane-01/05/06、灯台町の紹介文下書き・product.json・表紙指示・上位3本調べ・CG棚卸し・体験版指示書。画像・成人向けCGは入っていない）

## 指示書（優先順）
| # | ファイル | 一言 | 受け取り | 上限 |
|---|---|---|---|---|
| 01 | 01-konkatsu-06-12.md | 婚活10秒台本7本（10/30〜11/05分） | 動画部隊長 | 90分・直し3周 |
| 02 | 02-toudai-dlsite-text.md | 灯台町の契約 DLsite出品テキスト一式 | 同人部隊長（→規約係） | 90分・直し3周 |
| 03 | 03-pet-06-08.md | 猫10秒台本3本 | 動画部隊長 | 60分・直し3周 |
| 04 | 04-kane-11-13.md | 金メモ12秒型の試作台本3本（BGMあり） | 動画部隊長 | 60分・直し3周 |

4本とも並列で起動してよい（全部テキストだけ）。

## 今回入れなかったもの（理由）
- 美容: 01/04 は声のサンプル待ち（ElevenLabs→ナオミチが選ぶ）、02/03/05 は案件なし。台本を増やしても先に進まない。
- BOOTH出品文: 下書き5本（8994071〜8994231）の中身は BOOTH 管理画面（ログイン要）にあり、出品文は product JSON（2026-10-14-22〜25 の descriptions）にもうある。BOOTHは21日間 booth.pm 経由0・販売0で、文章より集客の問題（booth/sales/log.md）。
- Threads: 10/26〜11/01 分の下書きは箱にある。
- ねむり: お蔵入り（10/23）。
- サクラ・CG・体験版フォルダ作り・投稿・Driveアップ: PCかログインが要る。
