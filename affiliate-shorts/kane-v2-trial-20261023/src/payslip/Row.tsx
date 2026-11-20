import { BLUE } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PayslipRow = () => {
  return (
    <Frame tint={BLUE} caption="標準報酬月額、30万円の行。">
      <FactBlock top={420}>
        <Sub size={48}>標準報酬月額</Sub>
        <Hero size={140}>
          30
          <span style={{ fontSize: 80 }}>万円</span>
        </Hero>
        <Sub size={48}>この行の折半額</Sub>
        <Hero size={96} color="#3A2A22">
          27,450円
        </Hero>
      </FactBlock>
    </Frame>
  );
};
