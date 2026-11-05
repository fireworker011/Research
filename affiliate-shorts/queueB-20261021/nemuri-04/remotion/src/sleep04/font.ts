import { loadFont } from "@remotion/google-fonts/KleeOne";

const loaded = loadFont("normal", {
  weights: ["600"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});

export const kleeFamily = loaded.fontFamily;
