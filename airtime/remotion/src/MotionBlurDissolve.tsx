import React from 'react';
import {AbsoluteFill, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

// The glasses -> piano transition of ADUM_6-q5Ks (catalog-tehnici.md, section 3): the old shot A moves up
// with motion blur while the new shot B dissolves in over 1.16 s with a focus pull. Keyframes are measured
// at 25 fps and kept here in seconds, so the move lasts the same time at any fps (PLAN, D-28).
// Pixel values are for 1080 px of height and scale with the composition height.
export type MotionBlurDissolveProps = {
  width: number;
  height: number;
  fps: number;
  a: string; // file in public/ or an http(s) URL
  b: string;
  aFrom?: number; // start offset in A and B, in frames
  bFrom?: number;
  tint?: boolean; // warm A / cool B, only for footage that lacks the difference (catalog, section 3)
};

export const MOTION_BLUR_DISSOLVE_SEC = 1.72; // 43 frames at 25 fps

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const src = (s: string) => (/^(https?:|data:|blob:)/.test(s) ? s : staticFile(s));

export const MotionBlurDissolve: React.FC<MotionBlurDissolveProps> = ({a, b, aFrom = 0, bFrom = 0, tint = false}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const t = frame / fps; // seconds since the move on A starts
  const u = height / 1080;
  const p = interpolate(t, [0, 0.08, 0.36, 0.4], [0, 0.13, 0.97, 1], clamp);
  const aY = (144 - 288 * p) * u; // scale 1.27 leaves 146 px of room above and below
  const aX = (60 - 120 * p) * u; // drift to the left
  const aBlur = interpolate(t, [0, 0.08, 0.28, 0.4, 0.8], [0, 0, 4, 10, 12], clamp) * u;
  const bOpacity = interpolate(t, [0.12, 1.28], [0, 1], clamp);
  const bBlur = interpolate(t, [0.12, 0.56, 1.68], [12, 12, 0], clamp) * u;
  const bX = (189 - 225 * t) * u; // -9 px per 25 fps frame; scale 1.2 leaves 192 px on each side
  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      <AbsoluteFill
        style={{
          scale: '1.27',
          translate: `${aX}px ${aY}px`,
          filter: `blur(${aBlur}px)${tint ? ' sepia(0.2) saturate(1.1)' : ''}`,
        }}
      >
        <OffthreadVideo src={src(a)} startFrom={aFrom} muted />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          opacity: bOpacity,
          scale: '1.2',
          translate: `${bX}px 0px`,
          filter: `blur(${bBlur}px)${tint ? ' hue-rotate(-10deg) brightness(1.15)' : ''}`,
        }}
      >
        <OffthreadVideo src={src(b)} startFrom={bFrom} muted />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
