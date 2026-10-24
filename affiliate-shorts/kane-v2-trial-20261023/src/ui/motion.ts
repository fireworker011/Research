import { Easing, interpolate, useCurrentFrame } from "remotion";

export const useEnter = () => {
  const frame = useCurrentFrame();
  return interpolate(frame, [0, 8], [0.94, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
};

export const useFloat = (amplitude = 8) => {
  const frame = useCurrentFrame();
  return Math.sin(frame / 16) * amplitude;
};
