import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Colors} from './Intro';

// CTA keyword for the reels, held to the last frame (PLAN, D-50, D-56).
// One pill centred at 48% of the height (inside the list area, which has faded out by then, D-53).
// Opacity ramps like the list items: 0.25 on frame 0, 0.5, 0.75, then 1 from frame 3; no fade-out.
// The font shrinks so that up to 30 characters stay on one line inside the pill.
export type CtaKeywordProps = {
  width: number;
  height: number;
  fps: number;
  colors: Colors;
  word: string;
  duration: number; // seconds, from from_s to the end of the reel
};

export const CTA_CENTER = 0.48;
export const CTA_HEIGHT = 0.12;

export const CtaKeyword: React.FC<CtaKeywordProps> = ({word, colors}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const unit = Math.min(width, height) / 100;
  const text = word.toUpperCase();
  const fontSize = Math.min(11 * unit, (width - 20 * unit) / (0.8 * Math.max(1, text.length)));
  const opacity = interpolate(frame, [-1, 3], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          top: height * (CTA_CENTER - CTA_HEIGHT / 2),
          height: height * CTA_HEIGHT,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            height: '100%',
            maxWidth: width - 12 * unit,
            display: 'flex',
            alignItems: 'center',
            padding: `0 ${4 * unit}px`,
            boxSizing: 'border-box',
            backgroundColor: colors.accent,
            borderRadius: 2 * unit,
            opacity,
            fontFamily: 'Helvetica, Arial, sans-serif',
            fontWeight: 800,
            fontSize,
            color: colors.primary,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
