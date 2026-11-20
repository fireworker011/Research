import { BigPayslip } from "../art/Objects";
import { BLUE } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PayslipHalf = () => {
  return (
    <Frame tint={BLUE} caption="厚生年金の、折半額。">
      <BigPayslip top={120} />
      <FactBlock top={700}>
        <Sub size={56}>厚生年金の折半額</Sub>
        <Hero size={132}>
          27,450
          <span style={{ fontSize: 72 }}>円</span>
        </Hero>
      </FactBlock>
    </Frame>
  );
};
