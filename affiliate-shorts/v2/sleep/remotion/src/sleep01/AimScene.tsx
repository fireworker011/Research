import { NightShell, SerifLine } from "./NightShell";

export const AimScene = () => {
  return (
    <NightShell>
      <SerifLine text="成人の目安は" size={52} color="#D5DCF0" weight={400} />
      <SerifLine text="6時間以上" size={120} color="#F4F0E6" />
      <SerifLine text="睡眠ガイド2023" size={44} color="#A9B4D4" weight={400} />
    </NightShell>
  );
};
