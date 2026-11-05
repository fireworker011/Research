import { CalendarBoard } from "../art/Objects";
import { YELLOW } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PensionAge = () => {
  return (
    <Frame tint={YELLOW} caption="原則、65歳からの満額。">
      <CalendarBoard label="65" top={180} />
      <FactBlock top={760}>
        <Sub size={48}>原則</Sub>
        <Hero size={88}>65歳からの満額</Hero>
      </FactBlock>
    </Frame>
  );
};
