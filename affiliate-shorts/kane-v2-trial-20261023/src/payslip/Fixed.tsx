import { CalendarBoard } from "../art/Objects";
import { YELLOW } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PayslipFixed = () => {
  return (
    <Frame tint={YELLOW} caption="平成29年9月から固定。">
      <CalendarBoard label="9" top={140} />
      <FactBlock top={680}>
        <Sub size={44}>平成29年9月</Sub>
        <Hero size={100}>固定</Hero>
      </FactBlock>
    </Frame>
  );
};
