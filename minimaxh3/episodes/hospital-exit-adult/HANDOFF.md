# 病棟出口 引き継ぎプロンプト

この文を Cursor でも Grok でも、そのまま最初の指示として貼る。チャット履歴は正本にしない。正本は下のファイルだけ。両方のツールは同じブランチの同じファイルを編集する。

## 役割

病棟出口 `hospital-exit-adult` の既存カットだけを直す。新しい話、新しいキャラ、投稿、トレードはしない。生成ボタンは人間が押す。こちらは台本・つなぎ・テストを合わせる。

## 正本（ここだけを編集する）

- リポジトリ: `fireworker011/Research`
- ブランチ: `cursor/h3-hospital-ward-34e4`
- PR: https://github.com/fireworker011/Research/pull/147
- Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-hospital-ward-34e4/minimax_h3_episode_bot.ipynb
- 台本: `minimaxh3/episodes/hospital-exit-adult/episode.json`
- エンジン: `colab/h3_episode.py` を直したら、同じ内容を `minimaxh3/h3_episode.py` にコピーする。片方だけ直さない
- Colab 入口: `colab/h3_episode_colab_main.py` と `minimaxh3/h3_episode_colab_main.py` も同様に揃える
- ノートのフォーム: `colab/_write_episode_nb.py` を直し、`python3 colab/_write_episode_nb.py` で `minimax_h3_episode_bot.ipynb` と `minimaxh3/minimax_h3_episode_bot.ipynb` を再生成する。ipynb を手で直さない
- テスト: `python3 -m pytest colab/test_h3_episode.py -q`
- このファイル: `minimaxh3/episodes/hospital-exit-adult/HANDOFF.md`。仕様が変わったら、ここを同じコミットで更新する

## プロンプトの書き方

- 英語の動作文。日本語は「」のセリフだけ
- 体位の名前は書かない。誰がどこへ動くかを書く
- 否定で消したいものを描かせない。`blood` `zombie` `corpse` は書かない。H3 は否定してもその語を描く
- 足が切れる参照動画があっても、画面は全身、両足まで入れる
- 数字は台本とテストに既にあるものだけ使う。尺や売上を新しく作らない

## つなぎ（確認済み）

Colab の「前の最終フレームから続ける」は `connect=chain`。

- 最初の GPU カットだけ T2V
- 遭遇カット（id が `-spot`）も I2V。前の最終フレームのあやに、新しい人が入る
- それ以外の GPU カットも、前の最終フレームからの I2V
- 同じ相手の次の行為、ポーズ、トイレ、灰色、角、戦いも I2V。台本の `connect: t2v` は、この病棟でチェーンを選んだときは効かない
- 「カット」を選ぶと全部 T2V
- 受け入れる＋灰色の騎乗＋角の立ちバック＋トイレ＋4人登場で測ると、T2V は `01-cover` だけ。遭遇も I2V

遭遇を足す関数は `insert_presence_beats`。`keep_chain_cast` は `-spot` の新人を T2V に戻さない。遭遇を消さず、遭遇自体を chain のままにする。

## 容姿

初期の見た目は `cast` の `lock`。そのカットだけ違うときは `cast_lock`。汚れ、傷、粘液、髪、肌の色、竿の長さと色はここに書く。

各病棟カットのプロンプトには `Look that stays for this whole shot` が付く。否定の句（`no` `never` `not` `without`）はそこから落とす。竿を消す歩きだけ、action に `No penis` と `The grown shaft is gone` と書く。その歩きには竿を戻さない。

チェーンの I2V は、前フレームが汚れや竿を落としていても、`subject_definitions` の見た目に戻す。

遭遇 `-spot` も同じ Look を付ける。action にあやの grimy brown hospital dirt を書く。

## ギンの騎乗（`灰色・犯される`）

- 遭遇 `04-gin-lick-spot` は I2V。前フレームのあやに続ける。ギンは画面左端から入る。視聴者から見てあやの左＝あやの真後ろを、あやの歩幅に合わせて歩く。あやの歩きは徐々遅くなり、恐る恐る立ち止まる。あやは右、ギンは左。天井から落ちる構図は使わない
- `04-gin-lick`: あやがギンのいる左へ体ごと恐る恐る振り向き、驚きの顔で尻餅。そこがゴール。最終はギンが左でしゃがみ舌が出、あやが右で座り両膝開き 24cm 真上。舌と 24cm 成長は尻餅の後に同じ。ギンは竿なし。右端は暗い通路が続く。壁という語は書かない
- `04-gin-jupo`: あやは座ったまま仰向けになる。両足はリノリウムに付き、画面に残る。24cm は股間から垂直に真上。ギンは腰の上に屈み、舌は口の中、唇でその垂直の竿を根元まで咬える。片手は根元を持つ。あやの顔は目を細めた惬惚の笑顔。最後のコマは、あやが仰向け、竿が真上、ギンが跪いて胸と竿を持ち、マンコが亀頭の真上。次の `04-gin-ride` の入り
- `04-gin-ride`: その続きの着座。この着座の動きは変えない
- 騎乗の絶頂は、竿を持つ側が仰向けのまま短い上向きの突き。腰は密着に戻り、根元から漏れる。画面はあや一人とギン一人。あやを増やさない

## 向き（キス・遭遇のあと）

向かい合いの最終フレームから後ろへ入るときは、先に相手が壁側へ体ごと回り、あやも同じ向きになる。胸はあやの背中。それから掌と膝、または壁に手。体位名は書かない。

## 口のカメラ

フェラはカメラを寄せない。距離は固定。あやの顔と相手の顔が全カット残る。全身、両足まで入れる。`zoom` と `Do not push the camera in` は書かない。正の文だけ。`07-oral` と `04-gin-jupo` も同じ。

## 騎乗のカメラ

横からの距離固定。あやの顔と相手の顔が残る。全身、両足。プロンプトの camera から `from directly above` は落とす。着座は横顔のまま腰が下る。

## かなの着座（`09-join-ride`）

口の最終コマは跪き、唇が根元。次の着座は跪きからかなを仰向けにして腰に座る。3段下ろし。口カットの途中で着座へ変形しない。

## ネルソン

向かい合い（口が付いたあと）から相手が後ろへ回り、両前腕を太腿の下へ入れて持ち上げる。画面はあやがカメラ向き、相手の顔はあやの頭の後ろ。足は空中。`feet leave the linoleum` は書かない。角は遭遇の立ち（後ろ、亀頭が肛門）から同じ持ち上げ。植えの性行為は大人2人、顔2つ。体を増やさない。

## 容姿の持ち越し

`Look that stays` の竿文は、lock に shaft / penis / Ncm がある人の名前だけ付ける。ギンの遭遇に竿文を足さない。

## メモリ

成功したカットの前に VRAM は下ろさない。メモリ不足でそのカットが失敗したときだけ下ろし、同じ尺をもう一度描く。それでも足りなければ短い尺に落とす。フォームに毎回解放のスイッチは置かない

## 作業の終わり

1. テストが通る
2. `colab/` と `minimaxh3/` の対応ファイルが同じ
3. このブランチへコミットして push
4. PR #147 の説明を、変わった事実だけ直す
5. 人間へ Colab リンクを返す。再生成は FRESH をオン。raw が既にあるカットは、FRESH がオフだと作り直さない
