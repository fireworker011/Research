import { loadFont } from "@remotion/google-fonts/NotoSansJP";

const sans = loadFont("normal", {
  weights: ["400", "700", "900"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});

export const sansFamily = sans.fontFamily;
