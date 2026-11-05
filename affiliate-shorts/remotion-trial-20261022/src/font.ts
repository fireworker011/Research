import { loadFont } from "@remotion/google-fonts/DelaGothicOne";
import { continueRender, delayRender } from "remotion";

const loaded = loadFont("normal", {
  weights: ["400"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});

const fontHandle = delayRender("dela-gothic-one");
void loaded.waitUntilDone().then(() => {
  continueRender(fontHandle);
});

export const FONT = loaded.fontFamily;
