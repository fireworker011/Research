import { loadFont } from "@remotion/google-fonts/NotoSerifJP";

const serif = loadFont("normal", {
  weights: ["400", "700"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});

export const serifFamily = serif.fontFamily;
