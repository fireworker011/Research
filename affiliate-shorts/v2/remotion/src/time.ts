import type { Cue } from "./cues";

export const activeCue = (list: Cue[], t: number): Cue => {
  for (const cue of list) {
    if (t >= cue.start && t < cue.end) {
      return cue;
    }
  }
  return list[list.length - 1];
};

export const cueIndex = (list: Cue[], t: number): number => {
  const cue = activeCue(list, t);
  return list.indexOf(cue);
};
