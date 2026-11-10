import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Colors} from './Intro';

export type ListOverlayProps = {
  width: number;
  height: number;
  fps: number;
  colors: Colors;
  items: string[];
};

// Transparent card at the right edge; items appear one after another over 5 s.
export const ListOverlay: React.FC<ListOverlayProps> = ({items, colors}) => {
  const frame = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();
  const unit = Math.min(width, height) / 100;
  const out = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stagger = Math.min(fps * 0.5, (fps * 3) / Math.max(items.length, 1));
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'flex-end', padding: `0 ${5 * unit}px`}}>
      <div
        style={{
          backgroundColor: colors.primary,
          borderLeft: `${unit}px solid ${colors.accent}`,
          padding: `${2.5 * unit}px ${3 * unit}px`,
          maxWidth: '60%',
          opacity: out,
          fontFamily: 'Helvetica, Arial, sans-serif',
        }}
      >
        {items.map((item, i) => {
          const p = spring({frame: frame - i * stagger, fps, config: {damping: 200}});
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'baseline',
                gap: 1.6 * unit,
                color: '#ffffff',
                fontSize: 3.6 * unit,
                fontWeight: 600,
                lineHeight: 1.3,
                marginTop: i ? 1.4 * unit : 0,
                opacity: p,
                translate: `${(1 - p) * 4 * unit}px 0`,
              }}
            >
              <span style={{color: colors.accent, fontWeight: 800}}>{i + 1}.</span>
              <span>{item}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
