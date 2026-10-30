import React from "react";
import { Composition } from "remotion";
import { Split02 } from "./videos/Split02";
import { Stamp01 } from "./videos/Stamp01";
import { Ticket03 } from "./videos/Ticket03";

const fps = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Kane01"
        component={Stamp01}
        durationInFrames={22 * fps}
        fps={fps}
        width={1080}
        height={1920}
      />
      <Composition
        id="Kane02"
        component={Split02}
        durationInFrames={48 * fps}
        fps={fps}
        width={1080}
        height={1920}
      />
      <Composition
        id="Kane03"
        component={Ticket03}
        durationInFrames={34 * fps}
        fps={fps}
        width={1080}
        height={1920}
      />
    </>
  );
};
