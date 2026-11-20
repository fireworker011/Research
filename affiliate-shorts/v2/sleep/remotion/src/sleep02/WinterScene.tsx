import { DayShell, SansLine } from "./DayShell";

export const WinterScene = () => {
  return (
    <DayShell>
      <SansLine text="冬は18℃以上" size={84} color="#E23D12" />
      <SansLine text="WHO住環境ガイド" size={48} color="#1A120C" weight={700} />
      <SansLine text="睡眠ガイド2023が引用" size={44} color="#6B4A32" weight={400} />
    </DayShell>
  );
};
