import React from "react";
import { Composition } from "remotion";
import type { CalculateMetadataFunction } from "remotion";
import { KanememoVideo } from "./KanememoVideo";
import type { Mode, Spec, VideoProps } from "./types";
import kougakuJson from "../data/kougaku-hayamihyo.json";
import shussanJson from "../data/shussan-ichijikin.json";
import shobyoJson from "../data/shobyo-teate.json";
import nenkinJson from "../data/nenkin-kurisage.json";

const specs: Spec[] = [
  kougakuJson as Spec,
  shussanJson as Spec,
  shobyoJson as Spec,
  nenkinJson as Spec,
];

const assertNever = (value: never): never => {
  throw new Error(`unknown mode: ${String(value)}`);
};

const calculateMetadata: CalculateMetadataFunction<VideoProps> = async ({
  props,
}) => {
  if (props.mode === "overlay") {
    return {
      defaultCodec: "prores",
      defaultVideoImageFormat: "png",
      defaultPixelFormat: "yuva444p10le",
      defaultProResProfile: "4444",
    };
  }
  if (props.mode === "preview") {
    return {
      defaultCodec: "h264",
      defaultPixelFormat: "yuv420p",
      defaultVideoImageFormat: "jpeg",
    };
  }
  return assertNever(props.mode);
};

const composition = (spec: Spec, mode: Mode) => {
  const id = `${spec.slug}-${mode === "overlay" ? "overlay" : "preview"}`;
  return (
    <Composition
      key={id}
      id={id}
      component={KanememoVideo}
      width={1080}
      height={1920}
      fps={spec.fps}
      durationInFrames={Math.round(spec.durationSec * spec.fps)}
      defaultProps={{ spec, mode }}
      calculateMetadata={calculateMetadata}
    />
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {specs.map((spec) => (
        <React.Fragment key={spec.slug}>
          {composition(spec, "overlay")}
          {composition(spec, "preview")}
        </React.Fragment>
      ))}
    </>
  );
};
