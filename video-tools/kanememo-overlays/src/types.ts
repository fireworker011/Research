export type Window = {
  fromSec: number;
  toSec: number;
};

export type SubtitleCue = {
  fromSec: number;
  toSec: number;
  pos: "top" | "bottom";
  lines: string[];
};

export type TableRow = {
  fromSec: number;
  label: string;
  amount: string;
  faintLabel?: string;
  faintAmount?: string;
  detailLead?: string;
  detailRest?: string;
  tag?: string;
  emphasizeLead?: Window;
  highlight?: Window[];
};

export type Note = {
  fromSec: number;
  toSec: number;
  lines: string[];
  emphasize?: Window;
};

export type Spec = {
  slug: string;
  durationSec: number;
  fps: number;
  callout: {
    fromSec: number;
    toSec: number;
    lines: string[];
    sub?: string;
  };
  heading: {
    fromSec: number;
    toSec: number;
    text: string;
  };
  columns: [string, string];
  rows: TableRow[];
  notes: Note[];
  source: {
    fromSec: number;
    toSec: number;
    text: string;
  };
  credit: {
    fromSec: number;
    toSec: number;
    text: string;
  };
  subtitles: SubtitleCue[];
};

export type Mode = "overlay" | "preview";

export type VideoProps = {
  spec: Spec;
  mode: Mode;
};
