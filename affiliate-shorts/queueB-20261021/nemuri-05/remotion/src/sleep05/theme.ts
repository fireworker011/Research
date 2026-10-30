/** Picture only. No people, no lux numbers, no subtitle sentences. */
export const GOLD = "#F0C36A";
export const NAVY = "#10182C";
export const INK = "#FFF6E3";

export const FPS = 30;
export const OPEN_END = 60;
export const DAY_END = 210;
export const ROOM_END = 360;
export const BATH_END = 510;
export const TOTAL = 570;

export const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

export const breath = (frame: number, base: number, amp = 1.2) =>
  base + Math.sin(frame / 13) * amp;

export const mixHex = (from: string, to: string, t: number) => {
  const channel = (hex: string, index: number) => parseInt(hex.slice(index, index + 2), 16);
  const mixed = [1, 3, 5].map((index) => {
    const value = channel(from, index) + (channel(to, index) - channel(from, index)) * t;
    return Math.round(value).toString(16).padStart(2, "0");
  });
  return `#${mixed.join("")}`;
};
