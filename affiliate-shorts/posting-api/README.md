# 投稿APIの準備

自チャンネルへ動画を出すための手順とスクリプト。登録、許可、審査申請、投稿はしない。実行するのはナオミチ。定期実行にも、GitHub Actions にも載せない。

初期状態はドライラン。送るときは `--publish` を付ける。CI では `--publish` と `--fetch` を拒否する。

| 文書 | 内容 |
| --- | --- |
| [SETUP_YOUTUBE.md](SETUP_YOUTUBE.md) | Google Cloud、OAuth、枠、監査 |
| [SETUP_TIKTOK.md](SETUP_TIKTOK.md) | TikTok for Developers、Direct Post、審査前の制限 |
| [review/APPLICATION_DRAFT.md](review/APPLICATION_DRAFT.md) | 審査に貼る文 |
| [review/index.html](review/index.html) | プライバシーポリシーと利用規約の公開用ページ |

仕様の確認日は 2026-10-21。数字の出典は各 SETUP のURL。

## 全体の流れ

1. `review/` の `[運営者名]` `[連絡先メール]` `[公開日]` を埋める。`review/*.html` を別の公開リポジトリの `docs/` にコピーし、GitHub Pages を有効にする。この Research リポジトリは Pages にしない。
2. YouTube は Googleアカウントごとにプロジェクトと OAuth クライアントが既にある。下の PowerShell を、許可するチャンネルの順に1本ずつ実行する。よるの棚は保留。fireworker012 の YouTube は名前が決まるまで実行しない。
3. TikTok はアプリを1つ作り、Sandbox に6アカウントを追加し、`auth_tiktok.py` を1回ずつ実行する。
4. ドライランで文言と公開範囲を確認する。
5. 本番は `--publish`。結果のURLは `posted.csv`。このファイルは gitignore 済み。
6. 再生数は `fetch_stats.py --fetch`。クリック数はどちらのAPIにも無い。A8のクリックはA8の管理画面だけ。列は空のままにする。

YouTube のクライアントJSONは `C:\Users\hp\Downloads\youtube\<アカウント名>\client_secret_*.json`。トークンは同じフォルダの `token.json`、または `tokens/youtube/<key>.json`。TikTok のクライアントとトークンは `secrets/` と `tokens/`。環境変数でも渡せる。どれもコミットしない。`git add -f` で足さない。

説明欄に載せるのは開示の文。アフィURLはプロフィールに置く。`a8.net` が説明にあるとスクリプトが止まる。

A8の動画は `--a8`。説明に「アフィリエイト広告を含みます」が無いと止まる。

## ナオミチの手作業

YouTube のプロジェクトと OAuth クライアントは、Googleアカウントごとに作ってある。PCで押すのは許可だけ。ボタンの順とフォルダは [SETUP_YOUTUBE.md](SETUP_YOUTUBE.md)。

| サービス | key | 名前 | ログインの目印 | 状態 |
| --- | --- | --- | --- | --- |
| YouTube | pet_story_select | @pet_story_select | fireworker01 | 許可する |
| YouTube | yoru_neko_camera | よるのねこカメラ日記 | fireworker06 | 許可する |
| YouTube | sonae_30 | 30秒そなえ帳 | fireworker04 | 許可する |
| YouTube | nemuri_no_tana | ねむりの棚 | fireworker011 | 許可する |
| YouTube | pet_kurasu_monogatari | ペットと暮らす小さな物語 | naomichi235 | 許可する。チャンネルは新規作成中 |
| YouTube | yoru_no_tana | よるの棚 / @夜の棚 | 未定 | 保留。許可しない |
| YouTube | fireworker012_reserved | 未定 | fireworker012 | 名前が決まるまで許可しない |
| TikTok | yoru_no_tana | 夜の棚 | fireworker013 | 許可する |
| TikTok | uchi_no_fukuro | うちの袋 | fireworker04 | 許可する |
| TikTok | pet_chiisana_monogatari | ペットと暮らす小さな物語り | okadatakeshi510 | 許可する。YouTubeの pet_kurasu_monogatari とは別 |
| TikTok | yua | ゆあ | fireworker012 | 許可する。YouTubeの予約枠とは別 |
| TikTok | moto_konkatsu_miki | 元婚活難民ミキ | fireworker01 | 許可する |
| TikTok | kane_memo | 金メモ | fireworker02 | 許可する |

fireworker01 と fireworker04 は YouTube と TikTok の両方に出る。許可はサービスごとに別。fireworker012 は TikTok のゆあと、名前未定の YouTube 枠で別。

よるの棚の YouTube はアカウント未定。`channels.json` にメールアドレスは書かない。

TikTok の Sandbox 追加とアプリ審査のボタンは [SETUP_TIKTOK.md](SETUP_TIKTOK.md)。

## 依存

Python 3.11 以上。標準ライブラリだけ。`pip install` は無い。`requirements.txt` にその1行がある。

Windows では PowerShell から `py -3` を使う。`py -3 --version` で 3.11 以上と出ること。ランチャーが無いPCでは `py -3` を `python` に替える。

## PCでYouTubeを順に許可する

リポジトリのルートで開く。1本ずつ実行する。URLが出たら、そのGoogleアカウントの InPrivate ウィンドウに貼る。既定のブラウザは開かない。同意画面では、その動画のチャンネルを選ぶ。各許可は300秒以内。同じPCで開く。

```powershell
cd affiliate-shorts\posting-api
py -3 --version

py -3 auth_youtube.py --channel pet_story_select --client-dir "C:\Users\hp\Downloads\youtube\fireworker01" --no-browser
py -3 auth_youtube.py --channel yoru_neko_camera --client-dir "C:\Users\hp\Downloads\youtube\fireworker06" --no-browser
py -3 auth_youtube.py --channel sonae_30 --client-dir "C:\Users\hp\Downloads\youtube\fireworker04" --no-browser
py -3 auth_youtube.py --channel nemuri_no_tana --client-dir "C:\Users\hp\Downloads\youtube\fireworker011" --no-browser
py -3 auth_youtube.py --channel pet_kurasu_monogatari --client-dir "C:\Users\hp\Downloads\youtube\naomichi235" --no-browser
```

naomichi235 はチャンネル作成中。チャンネルがまだ無いときは、作ってから同じコマンドをやり直す。

よるの棚（`yoru_no_tana`）はアカウント未定なので、この一覧に無い。実行すると「アカウント未定のため保留」で止まる。

fireworker012 の YouTube は名前未定なので、この一覧に無い。名前を `channels.json` の title に書いて `status` を `active` にしてから許可する。TikTok のゆあは別のコマンド。

期間内の再生数が要るチャンネルだけ、その1本の末尾に `--with-analytics` を付けてから実行する。後から足すと許可のやり直しになる。

トークンは `C:\Users\hp\Downloads\youtube\<アカウント名>\token.json` に保存される。

## コマンド

ドライラン（PowerShell）:

```powershell
cd affiliate-shorts\posting-api
py -3 upload_youtube.py `
  --channel pet_story_select `
  --video C:\path\to\video.mp4 `
  --title "タイトル" `
  --description "アフィリエイト広告を含みます" `
  --privacy private `
  --category-id 15 `
  --not-made-for-kids `
  --a8
```

`python3` がある環境では、`py -3` を `python3` に替えて同じ引数で動く。

送るときだけ、同じコマンドに `--publish` を足す。予約公開は `--schedule 2026-10-22T21:00:00+09:00`。タイムゾーン必須。YouTube はその時刻まで private で、時刻になると公開になる。

TikTok の下書き:

```powershell
py -3 upload_tiktok.py `
  --channel kane_memo `
  --video C:\path\to\video.mp4 `
  --title "タイトル" `
  --description "アフィリエイト広告を含みます" `
  --privacy private `
  --a8 `
  --inbox `
  --publish
```

`--inbox` ではキャプションも公開範囲もAPIで付かない。TikTokアプリの受信箱で入れる。開示の文もそこで入れる。

再生数:

```powershell
py -3 fetch_stats.py --from-csv posted.csv --fetch
```

`--analytics` は、許可時に `auth_youtube.py --with-analytics` したトークンだけ。期間内の再生数で、累計とは別の列になる。

カテゴリIDは `videoCategories.list`（`regionCode=JP`）の番号。スクリプトは数字であることだけ見る。

子ども向けにするかはチャンネルごとに選ぶ。意図が無ければ `--not-made-for-kids`。

AI生成なら YouTube も TikTok も `--synthetic-media`。

同じファイルの再送は、`posted.csv` に成功行があると止まる。意図してやり直すときだけ `--allow-duplicate`。

## 審査の期間

公式が日数を書いているものだけを書く。保証ではない、と各ページにある。

- Google のブランド確認: 2〜3営業日。機微スコープ: サポートの表では10営業日。開発者向けページは通常3〜5営業日。制限付きスコープ: 約6週間。追加したスコープがどちらかは同意画面の表が正。
  - https://support.google.com/cloud/answer/13463817
  - https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification
- YouTube API のコンプライアンス監査: 日数の記載は無い。「as soon as possible」。OAuthの確認とは別で、既定の1日100アップロードを超えるときに使う。
  - https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits
- TikTok のアプリ審査: 審査ガイドラインに日数の記載は無い。個人利用のアプリは承認しない、と書いてある。
  - https://developers.tiktok.com/docs/en/app-review-guidelines

## 審査が終わるまでの出し方

YouTube: `--privacy private` で上げ、YouTube Studio で公開に切り替える。予約なら `--schedule`。現行の `videos.insert` は、未監査でも非公開ロックはしない、と書いている。2020-07-28 の履歴には逆の文が残っている。ロックされた動画は Studio で公開にする。

TikTok: `--inbox` で下書きを送る。TikTokアプリの受信箱から投稿する。審査前の Direct Post は、非公開アカウントの自分だけが見える投稿に限られる。

## テスト

```powershell
cd affiliate-shorts\posting-api
py -3 -m unittest test_posting.py
```

ネットワークの YouTube / TikTok は呼ばない。
