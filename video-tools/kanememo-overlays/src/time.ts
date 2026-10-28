export const isOn = (
  frame: number,
  fps: number,
  fromSec: number,
  toSec: number,
): boolean => {
  const t = frame / fps;
  return t >= fromSec && t < toSec;
};
