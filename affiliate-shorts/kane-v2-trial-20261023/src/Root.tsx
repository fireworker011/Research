import { Composition, Folder } from "remotion";
import { PensionAge } from "./pension/Age";
import { PensionBirth } from "./pension/Birth";
import { PensionClaim } from "./pension/Claim";
import { PensionEarlier } from "./pension/Earlier";
import { PensionHook } from "./pension/Hook";
import { PensionName } from "./pension/Name";
import { PensionSince } from "./pension/Since";
import { PensionYears } from "./pension/Years";
import { PensionVideo } from "./PensionVideo";
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
import { PayslipVideo } from "./PayslipVideo";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="Payslip27450"
        component={PayslipVideo}
        durationInFrames={549}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Pension70608"
        component={PensionVideo}
        durationInFrames={527}
        fps={30}
        width={1080}
        height={1920}
      />
      <Folder name="PayslipScenes">
        <Composition
          id="PayslipHook"
          component={PayslipHook}
          durationInFrames={43}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PayslipSlip"
          component={PayslipSlip}
          durationInFrames={40}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PayslipHalf"
          component={PayslipHalf}
          durationInFrames={49}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PayslipRow"
          component={PayslipRow}
          durationInFrames={72}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PayslipRange"
          component={PayslipRange}
          durationInFrames={86}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PayslipLevel"
          component={PayslipLevel}
          durationInFrames={35}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PayslipTotal"
          component={PayslipTotal}
          durationInFrames={59}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PayslipFund"
          component={PayslipFund}
          durationInFrames={57}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PayslipRate"
          component={PayslipRate}
          durationInFrames={46}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PayslipFixed"
          component={PayslipFixed}
          durationInFrames={62}
          fps={30}
          width={1080}
          height={1920}
        />
      </Folder>
      <Folder name="PensionScenes">
        <Composition
          id="PensionHook"
          component={PensionHook}
          durationInFrames={35}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PensionAge"
          component={PensionAge}
          durationInFrames={62}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PensionName"
          component={PensionName}
          durationInFrames={35}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PensionBirth"
          component={PensionBirth}
          durationInFrames={67}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PensionYears"
          component={PensionYears}
          durationInFrames={73}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PensionClaim"
          component={PensionClaim}
          durationInFrames={52}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PensionEarlier"
          component={PensionEarlier}
          durationInFrames={111}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="PensionSince"
          component={PensionSince}
          durationInFrames={92}
          fps={30}
          width={1080}
          height={1920}
        />
      </Folder>
    </>
  );
};
