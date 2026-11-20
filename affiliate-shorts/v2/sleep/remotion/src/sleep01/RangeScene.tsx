import { NightShell, SerifLine } from "./NightShell";

export const RangeScene = () => {
  return (
    <NightShell>
      <SerifLine text="適正はおおよそ" size={52} color="#D5DCF0" weight={400} />
      <SerifLine text="6〜8時間" size={120} color="#F4F0E6" />
      <SerifLine text="個人差がある" size={52} color="#D5DCF0" weight={400} />
      <SerifLine text="睡眠ガイド2023" size={44} color="#A9B4D4" weight={400} />
    </NightShell>
  );
};
