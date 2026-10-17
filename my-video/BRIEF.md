---
workflow: general-video
flow: automation
storyboard: no
message: "夜の都市を、光の文字と一緒に飛び抜ける"
destination: desktop-demo
aspect: 1920x1080
language: ja
audience: "CursorでHyperFramesのモーショングラフィックスを再現したい人"
length: 30s
angle: spectacle
narration: no
---

## Intent

ナレーションなしの30秒。サイバーパンクな都市のフライスルーに、光るキネティックタイポグラフィ、光の軌跡、抽象的な3Dを重ねる。動きはGSAPの一時停止タイムラインと、時間だけで描くThree.jsでシークできる。書き出し先は `renders/demo.mp4`。

デスクトップで見るデモとして 1920×1080。ショートの縦画角はこの依頼に含まれていない。画面の言葉は日本語。機械側の計器だけラテン文字と数字。

## Assets

なし。都市・軌跡・立体は手順の中で描く。写真も音楽もナレーションも置かない。

## Customizations

- サイバーパンクな都市のフライスルー
- 光るキネティックタイポグラフィ
- 光の軌跡と抽象的な3D
- GSAPでシークできるアニメーション
- 約30秒
- `renders/demo.mp4` へ書き出す

## Notes

- 使い方の確認では HyperFrames の利用枠が `unsupported_harness` で不明。数値は置かず、依頼された30秒のまま作る。
- カタログに「都市の峡谷を飛ぶカメラ」も「時間の関数で描く3Dの光の軌跡」も無かった。文字の叩きつけは `headline-slam` があるが、同じ composition id を4回重ねるとタイムラインの登録が衝突する。叩きつけ・3フレームの衝撃・上への退出はホストの1本のタイムラインに写し、都市と軌跡は Three.js の `hf-seek` で描く。
- 見た目: 背景 `#0B132B`、文字 `#F4F7FF`、文字の光はマゼンタ `#F72585` の1色。シアンは都市の窓と軌跡だけ。書体は Noto Sans JP（言葉）と JetBrains Mono（計器）。どちらも同梱フォント。
- 焦点は飛ぶ街の消失点と、端に置いた大きな言葉。計器は四隅。
