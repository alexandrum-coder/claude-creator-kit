import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

// Hard pop-in title of ADUM_6-q5Ks (catalog-tehnici.md, section 4, item 5): full opacity from the first
// frame, no position or scale animation, no plate or outline, then a 12-frame fade-out. Transparent
// background; render.mjs renders it as ProRes 4444 with alpha and compose.py lays it over the clip.
export type TitlePopProps = {
  width: number;
  height: number;
  fps: number;
  text: string;
  hold?: number; // seconds at full opacity before the fade-out
  color?: string;
};

export const TITLE_POP_FADE_FRAMES = 12;
export const TITLE_POP_HOLD_SEC = 3.9;

export const TitlePop: React.FC<TitlePopProps> = ({text, color = '#EBC400'}) => {
  const frame = useCurrentFrame();
  const {width, height, durationInFrames} = useVideoConfig();
  const unit = Math.min(width, height) / 100;
  const opacity = interpolate(frame, [durationInFrames - TITLE_POP_FADE_FRAMES, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          top: '47%',
          left: 0,
          right: 0,
          translate: '0 -50%',
          textAlign: 'center',
          color,
          opacity,
          fontFamily: 'Helvetica, Arial, sans-serif',
          fontWeight: 800,
          fontSize: 9 * unit,
          letterSpacing: 0.04 * 9 * unit,
          textTransform: 'uppercase',
          lineHeight: 1.1,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
