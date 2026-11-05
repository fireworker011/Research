# 縦型ショート用 PR エンドカード

最後の 2 秒に載せる 9:16 のエンドカード。5 ジャンル × 3 種類。配色と動きは種類ごとに別。

一言は `line`、PR 表記は `prLabel`（初期値 `#PR`）。どちらもコンポジションの props で差し替える。

```tsx
import { Sequence, useVideoConfig } from "remotion";
import { PetPulse } from "./library";

export const Short = () => {
  const { fps } = useVideoConfig();
  return (
    <Sequence from={18 * fps} durationInFrames={2 * fps} premountFor={fps}>
      <PetPulse line="うちの子の留守中も見てみて" prLabel="#PR" />
    </Sequence>
  );
};
```

プレビューは `npm run dev`。mp4 は `npm run previews`（`previews/*.mp4`、1080×1920、30fps、2 秒）。

書体は `public/fonts/` の日本語サブセット（SIL Open Font License、`OFL.txt`）。種類ごとに別の書体。

投稿はしない。リンクは置かない。
