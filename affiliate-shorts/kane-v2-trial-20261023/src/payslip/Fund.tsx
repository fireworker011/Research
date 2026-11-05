import { MINT } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PayslipFund = () => {
  return (
    <Frame tint={MINT} caption="基金の加入員は、この表の外。">
      <FactBlock top={460}>
        <Sub size={44}>厚生年金基金の加入員</Sub>
        <Hero size={100}>この表の外</Hero>
      </FactBlock>
    </Frame>
  );
};
