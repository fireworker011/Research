import { BigPayslip } from "../art/Objects";
import { YELLOW } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero } from "../ui/Type";

export const PayslipSlip = () => {
  return (
    <Frame tint={YELLOW} caption="給料明細の数字です。">
      <BigPayslip top={180} />
      <FactBlock top={760}>
        <Hero size={96}>給料明細</Hero>
      </FactBlock>
    </Frame>
  );
};
