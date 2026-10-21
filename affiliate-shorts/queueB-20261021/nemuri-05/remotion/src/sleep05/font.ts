import { loadFont } from "@remotion/google-fonts/KaiseiDecol";

const loaded = loadFont("normal", {
  weights: ["700"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});

export const decolFamily = loaded.fontFamily;
