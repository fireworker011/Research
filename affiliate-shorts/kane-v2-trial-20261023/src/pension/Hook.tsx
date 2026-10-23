import { Person } from "../art/People";
import { CARDIGAN, HAIR_GRAY, YELLOW } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero } from "../ui/Type";

export const PensionHook = () => {
  return (
    <Frame tint={YELLOW} caption="70,608円。">
      <FactBlock top={150}>
        <Hero size={140}>
          70,608
          <span style={{ fontSize: 80 }}>円</span>
        </Hero>
      </FactBlock>
      <Person hair={HAIR_GRAY} shirt={CARDIGAN} hold="calendar" top={330} width={820} />
    </Frame>
  );
};
