import { YELLOW } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PayslipLevel = () => {
  return (
    <Frame tint={YELLOW} caption="第19等級です。">
      <FactBlock top={520}>
        <Sub size={48}>保険料額表</Sub>
        <Hero size={120}>第19等級</Hero>
      </FactBlock>
    </Frame>
  );
};
