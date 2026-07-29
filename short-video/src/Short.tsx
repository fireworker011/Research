import React, { useMemo } from 'react';
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from 'remotion';
import { Background, BackgroundSpec } from './components/Background';
import { EndCard, ProgressBar, Watermark } from './components/Overlays';
import { Telop } from './components/Telop';
import { loadJapaneseFont } from './load-font';
import { TelopStyle } from './theme';

export type Scene = {
  index: number;
  role: 'title' | 'body' | 'cta';
  telop: string;
  telopStyle: TelopStyle;
  narration: string;
  audioSrc: string;
  audioSeconds: number;
  audioStartFrame: number;
  durationInFrames: number;
  background: BackgroundSpec;
};

export type Timeline = {
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  durationSeconds: number;
  handle: string;
  ctaUrl: string;
  ctaLabel: string;
  caption: string;
  mockAudio: boolean;
  bgm: { src: string; volume: number; duckedVolume: number; seconds: number };
  scenes: Scene[];
};

export const Short: React.FC<{ timeline: Timeline }> = ({ timeline }) => {
  loadJapaneseFont();
  const { fps, durationInFrames } = useVideoConfig();

  // 各シーンの開始フレーム
  const starts = useMemo(() => {
    let acc = 0;
    return timeline.scenes.map((s) => {
      const from = acc;
      acc += s.durationInFrames;
      return from;
    });
  }, [timeline.scenes]);

  const bodyEnd = starts.length ? starts[starts.length - 1] + timeline.scenes[starts.length - 1].durationInFrames : 0;
  const xHandle = handleFromUrl(timeline.ctaUrl);

  // BGM のダッキング: ナレーションが鳴っている間は下げ、間では戻す。
  // 最後は 0 までフェードして、切れたような終わり方にしない。
  const speaking = useMemo(() => {
    const flags = new Array<boolean>(durationInFrames).fill(false);
    timeline.scenes.forEach((s, i) => {
      const from = starts[i] + s.audioStartFrame;
      const to = Math.min(durationInFrames, from + Math.round(s.audioSeconds * fps));
      for (let f = Math.max(0, from); f < to; f++) flags[f] = true;
    });
    return flags;
  }, [timeline.scenes, starts, durationInFrames, fps]);

  const bgmVolume = (frame: number) => {
    const ramp = Math.round(0.25 * fps); // 急に音量が変わると不自然なので少しなめらかに
    let target = speaking[frame] ? timeline.bgm.duckedVolume : timeline.bgm.volume;
    for (let d = 1; d <= ramp; d++) {
      if (speaking[frame - d] || speaking[frame + d]) {
        const blend = 1 - d / ramp;
        target = Math.min(target, timeline.bgm.volume - (timeline.bgm.volume - timeline.bgm.duckedVolume) * blend);
      }
    }
    const fadeIn = Math.min(1, frame / (0.8 * fps));
    const fadeOut = Math.min(1, Math.max(0, (durationInFrames - frame) / (1.0 * fps)));
    return target * fadeIn * fadeOut;
  };

  return (
    <AbsoluteFill style={{ backgroundColor: '#060a12' }}>
      {timeline.scenes.map((scene, i) => (
        <Sequence key={scene.index} from={starts[i]} durationInFrames={scene.durationInFrames}>
          <Background spec={scene.background} durationInFrames={scene.durationInFrames} />
          <Telop text={scene.telop} style={scene.telopStyle} durationInFrames={scene.durationInFrames} />
          <Sequence from={scene.audioStartFrame}>
            <Audio src={staticFile(scene.audioSrc)} />
          </Sequence>
        </Sequence>
      ))}

      {/* 本編のあとに残す締め。黒みではなく最後のシーンの続きに CTA を重ねる */}
      <Sequence from={bodyEnd}>
        <Background
          spec={timeline.scenes[timeline.scenes.length - 1].background}
          durationInFrames={durationInFrames - bodyEnd}
        />
        <EndCard label={timeline.ctaLabel} xHandle={xHandle} />
      </Sequence>

      <Watermark handle={timeline.handle} />
      <ProgressBar durationInFrames={durationInFrames} />

      <Audio src={staticFile(timeline.bgm.src)} volume={bgmVolume} />
    </AbsoluteFill>
  );
};

const handleFromUrl = (url: string) => {
  const name = url.match(/x\.com\/([A-Za-z0-9_]+)/)?.[1];
  return name ? `@${name}` : url;
};
