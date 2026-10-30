import { MINT } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PensionBirth = () => {
  return (
    <Frame tint={MINT} caption="昭和31年4月2日以後に生まれた人。">
      <FactBlock top={460}>
        <Sub size={44}>生まれた日</Sub>
        <Hero size={72}>昭和31年4月2日</Hero>
        <Hero size={80}>以後</Hero>
      </FactBlock>
    </Frame>
  );
};
