import { Folder } from "remotion";
import { BeautyFrameComposition } from "./cards/BeautyFrame";
import { BeautyRippleComposition } from "./cards/BeautyRipple";
import { BeautySheenComposition } from "./cards/BeautySheen";
import { MatchFlipComposition } from "./cards/MatchFlip";
import { MatchRibbonComposition } from "./cards/MatchRibbon";
import { MatchSpotComposition } from "./cards/MatchSpot";
import { MoneyReceiptComposition } from "./cards/MoneyReceipt";
import { MoneyStampComposition } from "./cards/MoneyStamp";
import { MoneyTickerComposition } from "./cards/MoneyTicker";
import { PetBounceComposition } from "./cards/PetBounce";
import { PetLampComposition } from "./cards/PetLamp";
import { PetPulseComposition } from "./cards/PetPulse";
import { SleepBreathComposition } from "./cards/SleepBreath";
import { SleepCurtainComposition } from "./cards/SleepCurtain";
import { SleepMoonComposition } from "./cards/SleepMoon";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="money">
        <MoneyStampComposition />
        <MoneyReceiptComposition />
        <MoneyTickerComposition />
      </Folder>
      <Folder name="pet">
        <PetPulseComposition />
        <PetLampComposition />
        <PetBounceComposition />
      </Folder>
      <Folder name="match">
        <MatchFlipComposition />
        <MatchRibbonComposition />
        <MatchSpotComposition />
      </Folder>
      <Folder name="beauty">
        <BeautySheenComposition />
        <BeautyRippleComposition />
        <BeautyFrameComposition />
      </Folder>
      <Folder name="sleep">
        <SleepMoonComposition />
        <SleepBreathComposition />
        <SleepCurtainComposition />
      </Folder>
    </>
  );
};
