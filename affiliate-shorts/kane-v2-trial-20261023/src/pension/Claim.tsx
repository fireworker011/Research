import { BLUE } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PensionClaim = () => {
  return (
    <Frame tint={BLUE} caption="繰上げも、繰下げもしない場合。">
      <FactBlock top={480}>
        <Sub size={48}>繰上げ</Sub>
        <Hero size={88}>しない</Hero>
        <Sub size={48}>繰下げ</Sub>
        <Hero size={88}>しない</Hero>
      </FactBlock>
    </Frame>
  );
};
