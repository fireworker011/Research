# TikTok の準備

確認日: 2026-10-21。開発者登録、アプリ作成、審査申請、許可、投稿はここではしない。押すのはナオミチ。

アプリは1つ。6アカウントは、それぞれがそのアプリを許可する。トークンはアカウントごとに別。

## いまの仕様

- 開発者サイト: https://developers.tiktok.com/
- アプリ作成: https://developers.tiktok.com/doc/getting-started-create-an-app
- Direct Post（すぐ投稿）: `video.publish`。`POST /v2/post/publish/video/init/`
  - https://developers.tiktok.com/doc/content-posting-api-get-started
  - https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- 下書き（受信箱）: `video.upload`。`POST /v2/post/publish/inbox/video/init/`。受信箱の通知をアプリで開いて、投稿を自分で終える。
  - https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
- 審査前の Direct Post は非公開だけ。
  - 24時間に投稿できるユーザーは5人まで。
  - 投稿するアカウントはその時点で非公開。
  - 公開範囲は `SELF_ONLY` だけ。あとから公開にするには、アカウントを公開にして、動画ごとの公開範囲を Everyone に変える。
  - クリエイターあたりの投稿上限はアカウントにより、目安は1日約15本。Direct Post を使う全クライアントで共有。
  - https://developers.tiktok.com/doc/content-sharing-guidelines
- 未処理の下書きは、24時間で5本まで。
- ユーザーの access token は、初期化が1分あたり6回まで。
- access token は24時間。refresh token は365日。更新で新しい refresh token が返ることがあり、スクリプトは返ったものを `tokens/` に上書きする。
  - https://developers.tiktok.com/doc/oauth-user-access-token-management （2026-08-04 更新）
- 予約時刻の項目は Direct Post にも inbox にも無い。予約は YouTube の `publishAt` だけ。
- キャプションは `post_info.title`。上限2200（UTF-16）。inbox はこの項目を送れない。
- A8は `--a8`。Direct Post では `brand_content_toggle=true`（第三者の有料プロモーション）と、キャプション内の「アフィリエイト広告を含みます」。`brand_organic_toggle` は自分の事業の宣伝なので、A8では false。
- AI生成は `--synthetic-media`。Direct Post の `is_aigc`。inbox ではアプリ側で付ける。
- 動画は MP4 / H.264 推奨。23〜60fps。辺は360〜4096。最大4GB。長さの上限はアカウントにより3分、5分、10分。APIが送れる最長は10分。
  - https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
- 5MB未満は1本で送る。64MB以下もこのスクリプトは1本で送る。それを超えると10,000,000バイトずつで、端数は最後のチャンクにまとめる。
- 再生数は `view_count`。ほかに `like_count`、`comment_count`、`share_count`。クリック数の項目は無い。
  - https://developers.tiktok.com/doc/tiktok-api-v2-video-object
  - https://developers.tiktok.com/doc/tiktok-api-v2-video-query
- スコープ: https://developers.tiktok.com/docs/en/tiktok-api-scopes
  - `user.info.basic` 表示名
  - `video.list` 再生数
  - `video.upload` 下書き
  - `video.publish` Direct Post

## 審査前に公開できない理由

審査ガイドライン: https://developers.tiktok.com/docs/en/app-review-guidelines

- アプリ名に TikTok など他社SNSの名を入れない。説明口調の名前（Video Uploader のようなもの）にもしない。
- 個人利用・私的利用のアプリは承認しない、と書いてある。開発中・テスト中も承認しない。
- このツールは自チャンネルへの投稿なので、その条項に当たる。審査は落ち得る。落ちても、下書き送信（inbox）と、各アカウントのTikTokアプリからの投稿は使える。審査文は、公開サービスであるように書き換えない。
- ウェブサイトのURLはログイン画面だけでは不可。プライバシーポリシーと利用規約のリンクが、メニューを開かずに見える。
- デモ動画は1本以上、最大5本、各50MBまで。未承認のアプリは Sandbox で撮る。申請したスコープを全部映す。使わないスコープは外す。外さないと審査が遅れる、と書いてある。
- 審査日数は、このガイドラインに書いていない。ポータルのステータスを見る。

Sandbox の対象ユーザーは10人まで。今回は6アカウントなので1つの Sandbox に収まる。
https://developers.tiktok.com/doc/add-a-sandbox

デスクトップの許可は PKCE。`code_challenge` は SHA-256 の16進。Base64 ではない。
https://developers.tiktok.com/doc/login-kit-desktop

リダイレクトURIは `http://127.0.0.1:8766/tiktok/callback`。localhost か 127.0.0.1、ポート必須、http 可。

## ナオミチが押す場所

アカウントが変わるたびに、そのTikTokでログインし直す。

1. https://developers.tiktok.com/ で開発者登録する。
2. アプリを作る。名前は「チャンネル机」など。アイコンを付ける。説明は `review/APPLICATION_DRAFT.md` のTikTok用。
3. 製品に Login Kit と Content Posting API を追加する。Direct Post の設定も、公開投稿を申請するときだけ有効にする。
4. デスクトップのリダイレクトURIに `http://127.0.0.1:8766/tiktok/callback` を入れる。
5. Sandbox settings → Target users → Add account。6アカウントを1つずつ追加する。追加後、表示まで1時間かかることがある。
6. Client key と Client secret を `secrets/tiktok-client.json` に置く。コミットしない。形は `examples/tiktok-client.example.json`。
7. まず下書きだけなら、スコープは `user.info.basic,video.list,video.upload` だけにする。`video.publish` はデモに映してから足す。

```bash
cd affiliate-shorts/posting-api
python3 auth_tiktok.py --channel yoru_no_tana --scopes user.info.basic,video.list,video.upload
```

表示名が `channels.json` の title と違うときは、title を表示名に直す。トークンは保存済み。

| key | 表示名 | ログインの目印 |
| --- | --- | --- |
| yoru_no_tana | 夜の棚 | fireworker013 |
| uchi_no_fukuro | うちの袋 | fireworker04 |
| pet_chiisana_monogatari | ペットと暮らす小さな物語り | okadatakeshi510 |
| yua | ゆあ | fireworker012 |
| moto_konkatsu_miki | 元婚活難民ミキ | fireworker01 |
| kane_memo | 金メモ | fireworker02 |

同じ目印が YouTube 側にもある（fireworker01、fireworker04）。許可は TikTok で別に取る。

8. 審査に出すときは、App review に次を入れる。
   - 各製品とスコープを、アプリの中でどう使うか。文面は `review/APPLICATION_DRAFT.md`。
   - Sandbox で撮ったデモ。許可 → 下書き送信、または Direct Post → 非公開で上がったこと。申請したスコープが全部映っていること。
   - プライバシーポリシーと利用規約の公開URL。`review/index.html` の先頭に両方のリンクがある。
9. Save のあと、Submit。

トークンの置き場は `tokens/tiktok/<key>.json`。環境変数は `TIKTOK_CLIENT_KEY`、`TIKTOK_CLIENT_SECRET`、`TIKTOK_REFRESH_TOKEN`。ファイルがあるときはファイルを使う。

審査が通るまで、送るなら `--inbox`。Direct Post は非公開アカウントの `SELF_ONLY` だけが通る。
