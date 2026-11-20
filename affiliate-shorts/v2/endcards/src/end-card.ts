import { z } from "zod";

export const END_CARD_WIDTH = 1080;
export const END_CARD_HEIGHT = 1920;
export const END_CARD_FPS = 30;
/** 2 seconds at 30fps. */
export const END_CARD_DURATION = 60;

export const endCardSchema = z.object({
  line: z.string(),
  prLabel: z.string(),
});

export type EndCardProps = z.infer<typeof endCardSchema>;
