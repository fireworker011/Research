import { YearTrack } from "../art/Objects";
import { DISPLAY } from "../font";
import { INK, YELLOW } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero } from "../ui/Type";

export const PensionYears = () => {
  return (
    <Frame tint={YELLOW} caption="20歳から60歳まで、40年納めたとき。">
      <YearTrack />
      <div
        style={{
          position: "absolute",
          left: 90,
          right: 90,
          top: 500,
          display: "flex",
          justifyContent: "space-between",
          fontFamily: DISPLAY,
          fontSize: 48,
          color: INK,
        }}
      >
        <span>20歳</span>
        <span>60歳</span>
      </div>
      <FactBlock top={680}>
        <Hero size={120}>40年</Hero>
      </FactBlock>
    </Frame>
  );
};
