import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Colors} from './Intro';

// Numbered list for the reels, each item shown on the word that names it (PLAN, D-45, H1-H3).
// Item k is its own pill on row k (top = 30% + k * 9% of the height), so nothing of it exists before its
// cue. Opacity ramps over 4 frames: 0 one frame before the cue, 0.25 on the cue frame, 1 from cue + 3.
// The list stays to the end of the overlay (the end of the reel) and fades out on the last 10 frames.
export type NumberedListProps = {
  width: number;
  height: number;
  fps: number;
  colors: Colors;
  items: {text: string; at: number}[]; // at = seconds from the start of the overlay
  duration: number; // seconds
};

export const NUMBERED_LIST_TOP = 0.3;
export const NUMBERED_LIST_ROW = 0.09;
const FADE_OUT_FRAMES = 10;

export const NumberedList: React.FC<NumberedListProps> = ({items, colors}) => {
  const frame = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();
  const unit = Math.min(width, height) / 100;
  const out = interpolate(frame, [durationInFrames - FADE_OUT_FRAMES, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill>
      {items.map((item, k) => {
        const cue = Math.round(item.at * fps);
        const inOp = interpolate(frame, [cue - 1, cue + 3], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        return (
          <div
            key={k}
            style={{
              position: 'absolute',
              left: 6 * unit,
              top: height * (NUMBERED_LIST_TOP + k * NUMBERED_LIST_ROW),
              height: height * NUMBERED_LIST_ROW * 0.8,
              maxWidth: width - 12 * unit,
              display: 'flex',
              alignItems: 'center',
              gap: 2.4 * unit,
              padding: `0 ${4 * unit}px`,
              boxSizing: 'border-box',
              backgroundColor: colors.primary,
              borderLeft: `${1.4 * unit}px solid ${colors.accent}`,
              opacity: inOp * out,
              fontFamily: 'Helvetica, Arial, sans-serif',
              fontWeight: 700,
              fontSize: 6 * unit,
              color: '#ffffff',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
            }}
          >
            <span style={{color: colors.accent, fontWeight: 800}}>{k + 1}.</span>
            <span>{item.text}</span>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
