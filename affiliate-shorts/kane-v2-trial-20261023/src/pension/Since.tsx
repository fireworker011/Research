import { CalendarBoard } from "../art/Objects";
import { YELLOW } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PensionSince = () => {
  return (
    <Frame tint={YELLOW} caption="70,608円は、令和8年4月分から。">
      <CalendarBoard label="4" top={120} />
      <FactBlock top={640}>
        <Hero size={100}>
          70,608
          <span style={{ fontSize: 60 }}>円</span>
        </Hero>
        <Sub size={44}>令和8年4月分から</Sub>
      </FactBlock>
    </Frame>
  );
};
