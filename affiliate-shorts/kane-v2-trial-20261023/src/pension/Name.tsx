import { BLUE } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PensionName = () => {
  return (
    <Frame tint={BLUE} caption="老齢基礎年金です。">
      <FactBlock top={560}>
        <Sub size={44}>この満額は</Sub>
        <Hero size={84}>老齢基礎年金</Hero>
      </FactBlock>
    </Frame>
  );
};
