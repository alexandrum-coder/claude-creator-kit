import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export type Colors = {primary: string; accent: string};
export type IntroProps = {
  width: number;
  height: number;
  fps: number;
  colors: Colors;
  title: string;
  channel: string;
  durationSec: number;
};

export const Intro: React.FC<IntroProps> = ({title, channel, colors}) => {
  const frame = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();
  const unit = Math.min(width, height) / 100;
  const bar = spring({frame, fps, config: {damping: 200}});
  const titleIn = spring({frame: frame - 10, fps, config: {damping: 200}});
  const channelIn = spring({frame: frame - 24, fps, config: {damping: 200}});
  const fadeOut = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{backgroundColor: colors.primary, justifyContent: 'center', alignItems: 'center'}}>
      <div style={{opacity: fadeOut, textAlign: 'center', padding: `0 ${8 * unit}px`, fontFamily: 'Helvetica, Arial, sans-serif'}}>
        <div style={{height: unit, width: 30 * unit * bar, backgroundColor: colors.accent, margin: `0 auto ${4 * unit}px`}} />
        <div
          style={{
            color: '#ffffff',
            fontSize: 7 * unit,
            fontWeight: 800,
            lineHeight: 1.15,
            opacity: titleIn,
            translate: `0 ${(1 - titleIn) * 3 * unit}px`,
          }}
        >
          {title}
        </div>
        <div
          style={{
            color: colors.accent,
            fontSize: 3.2 * unit,
            fontWeight: 600,
            letterSpacing: 0.4 * unit,
            marginTop: 3 * unit,
            opacity: channelIn,
          }}
        >
          {channel}
        </div>
      </div>
    </AbsoluteFill>
  );
};
