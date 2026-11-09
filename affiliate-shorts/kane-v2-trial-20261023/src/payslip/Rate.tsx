import { BLUE } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PayslipRate = () => {
  return (
    <Frame tint={BLUE} caption="率は18.3パーセント。">
      <FactBlock top={520}>
        <Sub size={48}>保険料率</Sub>
        <Hero size={160}>
          18.3
          <span style={{ fontSize: 88 }}>%</span>
        </Hero>
      </FactBlock>
    </Frame>
  );
};
