import { loadFont } from "@remotion/google-fonts/ZenMaruGothic";

const loaded = loadFont("normal", {
  weights: ["700"],
  subsets: ["japanese"],
  ignoreTooManyRequestsWarning: true,
});

export const maruFamily = loaded.fontFamily;
