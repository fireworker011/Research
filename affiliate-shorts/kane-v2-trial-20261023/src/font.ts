import { loadFont as loadDela } from "@remotion/google-fonts/DelaGothicOne";
import { loadFont as loadNoto } from "@remotion/google-fonts/NotoSansJP";
import { continueRender, delayRender } from "remotion";

const dela = loadDela("normal", {
  weights: ["400"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});

const noto = loadNoto("normal", {
  weights: ["700"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});

const delaHandle = delayRender("dela-gothic-one");
const notoHandle = delayRender("noto-sans-jp");
void dela.waitUntilDone().then(() => {
  continueRender(delaHandle);
});
void noto.waitUntilDone().then(() => {
  continueRender(notoHandle);
});

export const DISPLAY = dela.fontFamily;
export const CAPTION_FONT = noto.fontFamily;
