import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily, FontScope } from "./fonts";
import { isOn } from "./time";
import type { Mode, Note, Spec, SubtitleCue, TableRow, VideoProps } from "./types";

const ink = "#141414";

const assertNever = (value: never): never => {
  throw new Error(`unknown mode: ${String(value)}`);
};

const Callout: React.FC<{ spec: Spec; frame: number; fps: number }> = ({
  spec,
  frame,
  fps,
}) => {
  if (!isOn(frame, fps, spec.callout.fromSec, spec.callout.toSec)) {
    return null;
  }
  return (
    <div
      style={{
        position: "absolute",
        top: 400,
        left: 48,
        right: 48,
        backgroundColor: "#FFD400",
        border: "6px solid #111111",
        borderRadius: 28,
        padding: "28px 24px 24px",
        textAlign: "center",
        boxSizing: "border-box",
      }}
    >
      {spec.callout.lines.map((line) => (
        <div
          key={line}
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: 78,
            lineHeight: 1.12,
            color: ink,
          }}
        >
          {line}
        </div>
      ))}
      {spec.callout.sub ? (
        <div
          style={{
            marginTop: 10,
            fontFamily,
            fontWeight: 700,
            fontSize: 40,
            lineHeight: 1.2,
            color: ink,
          }}
        >
          {spec.callout.sub}
        </div>
      ) : null}
    </div>
  );
};

const RowView: React.FC<{
  row: TableRow;
  frame: number;
  fps: number;
}> = ({ row, frame, fps }) => {
  if (frame / fps < row.fromSec) {
    return null;
  }
  const hot = (row.highlight ?? []).some((window) =>
    isOn(frame, fps, window.fromSec, window.toSec),
  );
  const leadHot = row.emphasizeLead
    ? isOn(frame, fps, row.emphasizeLead.fromSec, row.emphasizeLead.toSec)
    : false;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1.05fr 0.95fr",
        columnGap: 12,
        alignItems: "center",
        backgroundColor: hot ? "#FFE14A" : "rgba(255,255,255,0.96)",
        border: hot ? "5px solid #111111" : "3px solid #222222",
        borderRadius: 18,
        padding: "14px 18px",
        boxSizing: "border-box",
      }}
    >
      <div>
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: 34,
            lineHeight: 1.25,
            color: ink,
            whiteSpace: "pre-line",
          }}
        >
          {row.label}
        </div>
        {row.faintLabel || row.faintAmount ? (
          <div
            style={{
              marginTop: 4,
              fontFamily,
              fontWeight: 700,
              fontSize: 24,
              lineHeight: 1.3,
              color: "#555555",
            }}
          >
            {row.faintLabel}
            {row.faintLabel && row.faintAmount ? " " : ""}
            {row.faintAmount}
          </div>
        ) : null}
      </div>
      <div style={{ textAlign: "right" }}>
        {row.detailLead || row.detailRest ? (
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: 26,
              lineHeight: 1.25,
              color: ink,
            }}
          >
            <span
              style={{
                backgroundColor: leadHot ? "#FFD400" : "transparent",
                borderRadius: 6,
                padding: leadHot ? "0 4px" : 0,
              }}
            >
              {row.detailLead}
            </span>
            {row.detailRest}
          </div>
        ) : null}
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: 52,
            lineHeight: 1.1,
            color: ink,
            whiteSpace: "nowrap",
          }}
        >
          {row.amount}
        </div>
        {row.tag ? (
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: 26,
              lineHeight: 1.2,
              color: ink,
            }}
          >
            {row.tag}
          </div>
        ) : null}
      </div>
    </div>
  );
};

const NoteView: React.FC<{ note: Note; frame: number; fps: number }> = ({
  note,
  frame,
  fps,
}) => {
  if (!isOn(frame, fps, note.fromSec, note.toSec)) {
    return null;
  }
  const hot = note.emphasize
    ? isOn(frame, fps, note.emphasize.fromSec, note.emphasize.toSec)
    : false;
  return (
    <div
      style={{
        backgroundColor: hot ? "#FFE14A" : "transparent",
        border: hot ? "4px solid #111111" : "none",
        borderRadius: 12,
        padding: hot ? "8px 12px" : "0 4px",
        boxSizing: "border-box",
      }}
    >
      {note.lines.map((line) => (
        <div
          key={line}
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: 28,
            lineHeight: 1.35,
            color: ink,
          }}
        >
          {line}
        </div>
      ))}
    </div>
  );
};

const TableBlock: React.FC<{ spec: Spec; frame: number; fps: number }> = ({
  spec,
  frame,
  fps,
}) => {
  if (!isOn(frame, fps, spec.heading.fromSec, spec.heading.toSec)) {
    return null;
  }
  return (
    <div
      style={{
        position: "absolute",
        top: 188,
        left: 36,
        right: 36,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <div
        style={{
          fontFamily,
          fontWeight: 700,
          fontSize: 34,
          lineHeight: 1.3,
          color: ink,
          backgroundColor: "rgba(255,255,255,0.96)",
          border: "3px solid #222222",
          borderRadius: 14,
          padding: "10px 14px",
        }}
      >
        {spec.heading.text}
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.05fr 0.95fr",
          columnGap: 12,
          padding: "0 8px",
        }}
      >
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: 28,
            color: ink,
          }}
        >
          {spec.columns[0]}
        </div>
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: 28,
            color: ink,
            textAlign: "right",
          }}
        >
          {spec.columns[1]}
        </div>
      </div>
      {spec.rows.map((row) => (
        <RowView key={row.label} row={row} frame={frame} fps={fps} />
      ))}
      {spec.notes.map((note) => (
        <NoteView key={note.lines.join("\n")} note={note} frame={frame} fps={fps} />
      ))}
    </div>
  );
};

const CornerLabel: React.FC<{
  show: boolean;
  text: string;
  side: "left" | "right";
  bottom: number;
}> = ({ show, text, side, bottom }) => {
  if (!show) {
    return null;
  }
  return (
    <div
      style={{
        position: "absolute",
        bottom,
        left: side === "left" ? 36 : undefined,
        right: side === "right" ? 36 : undefined,
        maxWidth: side === "right" ? 760 : 520,
        backgroundColor: "rgba(255,255,255,0.96)",
        border: "2px solid #222222",
        borderRadius: 10,
        padding: "6px 12px",
        fontFamily,
        fontWeight: 700,
        fontSize: 28,
        lineHeight: 1.3,
        color: ink,
        textAlign: side === "right" ? "right" : "left",
        boxSizing: "border-box",
      }}
    >
      {text}
    </div>
  );
};

const SubtitleLine: React.FC<{ cue: SubtitleCue }> = ({ cue }) => {
  if (cue.pos === "top") {
    return (
      <div
        style={{
          position: "absolute",
          top: 48,
          left: 40,
          right: 40,
          textAlign: "center",
        }}
      >
        {cue.lines.map((line, index) => (
          <div
            key={line}
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: index === 0 ? 54 : 34,
              lineHeight: 1.25,
              color: ink,
            }}
          >
            {line}
          </div>
        ))}
      </div>
    );
  }
  return (
    <div
      style={{
        position: "absolute",
        left: 36,
        right: 36,
        bottom: 48,
        textAlign: "center",
      }}
    >
      {cue.lines.map((line) => (
        <div
          key={line}
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: 46,
            lineHeight: 1.28,
            color: "#FFFFFF",
            WebkitTextStroke: "7px #111111",
            paintOrder: "stroke fill",
          }}
        >
          {line}
        </div>
      ))}
    </div>
  );
};

const Subtitles: React.FC<{ spec: Spec; frame: number; fps: number }> = ({
  spec,
  frame,
  fps,
}) => {
  const active = spec.subtitles.filter((cue) =>
    isOn(frame, fps, cue.fromSec, cue.toSec),
  );
  return (
    <>
      {active.map((cue) => (
        <SubtitleLine key={`${cue.pos}-${cue.fromSec}-${cue.lines[0] ?? ""}`} cue={cue} />
      ))}
    </>
  );
};

const Stage: React.FC<{ spec: Spec; mode: Mode }> = ({ spec, mode }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (fps !== spec.fps) {
    throw new Error(`fps mismatch: composition ${fps} spec ${spec.fps}`);
  }
  return (
    <>
      <Callout spec={spec} frame={frame} fps={fps} />
      <TableBlock spec={spec} frame={frame} fps={fps} />
      <CornerLabel
        show={isOn(frame, fps, spec.source.fromSec, spec.source.toSec)}
        text={spec.source.text}
        side="right"
        bottom={390}
      />
      <CornerLabel
        show={isOn(frame, fps, spec.credit.fromSec, spec.credit.toSec)}
        text={spec.credit.text}
        side="left"
        bottom={270}
      />
      {mode === "preview" ? (
        <Subtitles spec={spec} frame={frame} fps={fps} />
      ) : null}
    </>
  );
};

export const KanememoVideo: React.FC<VideoProps> = ({ spec, mode }) => {
  if (mode === "overlay") {
    return (
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        <FontScope>
          <Stage spec={spec} mode={mode} />
        </FontScope>
      </AbsoluteFill>
    );
  }
  if (mode === "preview") {
    return (
      <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
        <FontScope>
          <Stage spec={spec} mode={mode} />
        </FontScope>
      </AbsoluteFill>
    );
  }
  return assertNever(mode);
};
