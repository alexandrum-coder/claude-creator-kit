import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Colors} from './Intro';

export type ChapterTitleProps = {
  width: number;
  height: number;
  fps: number;
  colors: Colors;
  text: string;
};

// Transparent lower-third: accent bar and primary plate, slides in and fades out within 3 s.
export const ChapterTitle: React.FC<ChapterTitleProps> = ({text, colors}) => {
  const frame = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();
  const unit = Math.min(width, height) / 100;
  const inn = spring({frame, fps, config: {damping: 200}});
  const out = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'flex-start', padding: `0 ${6 * unit}px ${12 * unit}px`}}>
      <div
        style={{
          display: 'flex',
          opacity: inn * out,
          translate: `${(1 - inn) * -8 * unit}px 0`,
          fontFamily: 'Helvetica, Arial, sans-serif',
          maxWidth: '88%',
        }}
      >
        <div style={{width: unit, backgroundColor: colors.accent}} />
        <div
          style={{
            backgroundColor: colors.primary,
            color: '#ffffff',
            fontSize: 4.2 * unit,
            fontWeight: 700,
            padding: `${1.6 * unit}px ${3 * unit}px`,
            lineHeight: 1.2,
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
