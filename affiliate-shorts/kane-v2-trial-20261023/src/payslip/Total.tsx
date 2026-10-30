import { CoinPile } from "../art/Objects";
import { YELLOW } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PayslipTotal = () => {
  return (
    <Frame tint={YELLOW} caption="全額は、54,900円。">
      <CoinPile left={120} top={180} count={4} />
      <CoinPile left={680} top={180} count={4} />
      <FactBlock top={620}>
        <Sub size={56}>全額</Sub>
        <Hero size={128}>
          54,900
          <span style={{ fontSize: 72 }}>円</span>
        </Hero>
      </FactBlock>
    </Frame>
  );
};
