import { DayShell, SansLine } from "./DayShell";

export const DisclaimerScene = () => {
  return (
    <DayShell>
      <SansLine text="医療的な助言では" size={60} color="#1A120C" weight={700} />
      <SansLine text="ありません" size={72} color="#1A120C" />
    </DayShell>
  );
};
