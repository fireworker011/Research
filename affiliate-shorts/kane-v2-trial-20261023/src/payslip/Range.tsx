import { MINT } from "../theme";
import { Frame } from "../ui/Frame";
import { FactBlock, Hero, Sub } from "../ui/Type";

export const PayslipRange = () => {
  return (
    <Frame tint={MINT} caption="報酬は29万円以上、31万円未満。">
      <FactBlock top={460}>
        <Sub size={48}>報酬月額</Sub>
        <Hero size={96}>29万円以上</Hero>
        <Hero size={96}>31万円未満</Hero>
      </FactBlock>
    </Frame>
  );
};
