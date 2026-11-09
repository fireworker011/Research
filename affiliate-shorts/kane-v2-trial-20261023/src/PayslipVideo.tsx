import { Audio } from "@remotion/media";
import { AbsoluteFill, Series, staticFile, useVideoConfig } from "remotion";
import { PayslipFixed } from "./payslip/Fixed";
import { PayslipFund } from "./payslip/Fund";
import { PayslipHalf } from "./payslip/Half";
import { PayslipHook } from "./payslip/Hook";
import { PayslipLevel } from "./payslip/Level";
import { PayslipRange } from "./payslip/Range";
import { PayslipRate } from "./payslip/Rate";
import { PayslipRow } from "./payslip/Row";
import { PayslipSlip } from "./payslip/Slip";
import { PayslipTotal } from "./payslip/Total";

export const PayslipVideo = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={43} premountFor={fps} name="Hook">
          <PayslipHook />
        </Series.Sequence>
        <Series.Sequence durationInFrames={40} premountFor={fps} name="Slip">
          <PayslipSlip />
        </Series.Sequence>
        <Series.Sequence durationInFrames={49} premountFor={fps} name="Half">
          <PayslipHalf />
        </Series.Sequence>
        <Series.Sequence durationInFrames={72} premountFor={fps} name="Row">
          <PayslipRow />
        </Series.Sequence>
        <Series.Sequence durationInFrames={86} premountFor={fps} name="Range">
          <PayslipRange />
        </Series.Sequence>
        <Series.Sequence durationInFrames={35} premountFor={fps} name="Level">
          <PayslipLevel />
        </Series.Sequence>
        <Series.Sequence durationInFrames={59} premountFor={fps} name="Total">
          <PayslipTotal />
        </Series.Sequence>
        <Series.Sequence durationInFrames={57} premountFor={fps} name="Fund">
          <PayslipFund />
        </Series.Sequence>
        <Series.Sequence durationInFrames={46} premountFor={fps} name="Rate">
          <PayslipRate />
        </Series.Sequence>
        <Series.Sequence durationInFrames={62} premountFor={fps} name="Fixed">
          <PayslipFixed />
        </Series.Sequence>
      </Series>
      <Audio src={staticFile("narration-payslip.wav")} />
      <Audio src={staticFile("bgm-payslip.wav")} />
    </AbsoluteFill>
  );
};
