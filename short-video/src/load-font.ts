import { continueRender, delayRender, staticFile } from 'remotion';

// 日本語フォントを読み終える前にフレームを描くと豆腐（□）になるので、
// 読み込み完了までレンダリングを待たせる。
let handle: number | null = null;

export const loadJapaneseFont = () => {
  if (handle !== null) return;
  handle = delayRender('日本語フォントの読み込み');

  const font = new FontFace('ShortJP', `url(${staticFile('fonts/IPAGothic.ttf')}) format("truetype")`);

  font
    .load()
    .then((loaded) => {
      (document.fonts as unknown as { add: (f: FontFace) => void }).add(loaded);
      return document.fonts.ready;
    })
    .then(() => continueRender(handle as number))
    .catch((err) => {
      // フォントが無くてもフォールバック指定で描けるので、レンダリング自体は続行する
      console.warn('フォント読み込みに失敗、フォールバックで描画します:', err);
      continueRender(handle as number);
    });
};
