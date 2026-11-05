import { NightShell, SerifLine } from "./NightShell";

export const SurveyScene = () => {
  return (
    <NightShell>
      <SerifLine text="各世代で" size={48} color="#D5DCF0" weight={400} />
      <SerifLine text="約35〜50%" size={108} color="#F4F0E6" />
      <SerifLine text="20〜59歳は6時間未満" size={46} color="#D5DCF0" weight={400} />
      <SerifLine text="令和元年の栄養調査" size={44} color="#A9B4D4" weight={400} />
      <SerifLine text="睡眠ガイド2023が引用" size={44} color="#A9B4D4" weight={400} />
    </NightShell>
  );
};
