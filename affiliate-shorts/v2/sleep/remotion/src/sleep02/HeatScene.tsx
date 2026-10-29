import { DayShell, SansLine } from "./DayShell";

export const HeatScene = () => {
  return (
    <DayShell>
      <SansLine text="室温が上がると" size={72} color="#1A120C" />
      <SansLine text="睡眠時間は短く" size={64} color="#1A120C" weight={700} />
      <SansLine text="効率も下がった" size={64} color="#E23D12" />
      <SansLine text="睡眠ガイド2023" size={44} color="#6B4A32" weight={400} />
    </DayShell>
  );
};
