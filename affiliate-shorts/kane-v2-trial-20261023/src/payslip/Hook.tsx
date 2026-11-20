import { Person } from "../art/People";
import { HAIR, SHIRT, YELLOW } from "../theme";
import { FactBlock, Hero } from "../ui/Type";
import { Frame } from "../ui/Frame";

export const PayslipHook = () => {
  return (
    <Frame tint={YELLOW} caption="27,450円。">
      <FactBlock top={150}>
        <Hero size={150}>
          27,450
          <span style={{ fontSize: 84 }}>円</span>
        </Hero>
      </FactBlock>
      <Person hair={HAIR} shirt={SHIRT} hold="payslip" top={330} width={820} />
    </Frame>
  );
};
