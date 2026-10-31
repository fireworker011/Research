import React, { useEffect, useState } from "react";
import { continueRender, delayRender, staticFile } from "remotion";

const loadFonts = async (): Promise<void> => {
  const jp = new FontFace(
    "Kanememo",
    `url(${staticFile("fonts/NotoSansJP-700.woff")})`,
    { weight: "700", style: "normal" },
  );
  const symbols = new FontFace(
    "KanememoSymbols",
    `url(${staticFile("fonts/symbols-fallback.ttf")})`,
    { weight: "700", style: "normal" },
  );
  const [jpFace, symbolFace] = await Promise.all([jp.load(), symbols.load()]);
  document.fonts.add(jpFace);
  document.fonts.add(symbolFace);
  await document.fonts.ready;
};

export const fontFamily = '"Kanememo", "KanememoSymbols", sans-serif';

export const FontScope: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [handle] = useState(() => delayRender("kanememo-font"));
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let alive = true;
    loadFonts()
      .then(() => {
        if (alive) {
          setReady(true);
        }
      })
      .catch((error: unknown) => {
        console.error(error);
        if (alive) {
          setReady(true);
        }
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (ready) {
      continueRender(handle);
    }
  }, [ready, handle]);

  if (!ready) {
    return null;
  }
  return <>{children}</>;
};
