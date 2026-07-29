import React from 'react';
import { Composition } from 'remotion';
import { Short, Timeline } from './Short';
import timelineJson from '../public/timeline.json';

// public/timeline.json は scripts/build-timeline.mjs が生成する。
// 台本や音声を作り直したら `npm run timeline` を流せば尺も自動で追従する。
const timeline = timelineJson as unknown as Timeline;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    durationInFrames={timeline.durationInFrames}
    fps={timeline.fps}
    width={timeline.width}
    height={timeline.height}
    defaultProps={{ timeline }}
  />
);
