import { MINT } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PensionEarlier = () => {
  return (
    <Frame tint={MINT} caption="昭和31年4月1日以前の生まれは、月70,408円。">
      <FactBlock top={400}>
        <Sub size={40}>昭和31年4月1日以前</Sub>
        <Hero size={120}>
          70,408
          <span style={{ fontSize: 68 }}>円</span>
        </Hero>
        <Sub size={44}>月額の満額</Sub>
      </FactBlock>
    </Frame>
  );
};
