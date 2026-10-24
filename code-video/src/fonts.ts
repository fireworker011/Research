import { cancelRender, continueRender, delayRender, staticFile } from "remotion";

export const sans = "Noto Sans JP";
export const mono = "IBM Plex Mono";

const LATIN_RANGE =
  "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2190-21FF, U+2212, U+2215";

const loadFace = (
  family: string,
  file: string,
  weight: string,
  unicodeRange?: string,
) => {
  const face = new FontFace(family, `url(${staticFile(file)})`, {
    weight,
    style: "normal",
    unicodeRange,
  });
  return face.load().then((loaded) => {
    const fonts = document.fonts as FontFaceSet & {
      add: (font: FontFace) => void;
    };
    fonts.add(loaded);
  });
};

if (typeof document !== "undefined") {
  const handle = delayRender("fonts");
  void Promise.all([
    loadFace(sans, "noto-sans-jp-900.woff2", "900"),
    loadFace(sans, "noto-sans-jp-500.woff2", "500"),
    loadFace(sans, "noto-sans-jp-latin-900.woff2", "900", LATIN_RANGE),
    loadFace(sans, "noto-sans-jp-latin-500.woff2", "500", LATIN_RANGE),
    loadFace(mono, "ibm-plex-mono-500.woff2", "500"),
  ])
    .then(() => {
      continueRender(handle);
    })
    .catch((error: unknown) => {
      cancelRender(error);
    });
}
