import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';

// Impact caption mask for the reels (PLAN, Note 2.20, D-58, P4): white text on opaque black, no alpha.
// reels_fx.impact_args blends it into the reel with a difference blend: black changes nothing, white inverts.
// Each item is visible exactly in frames [from, from + dur), with a hard cut; the band is centred at 22%
// of the height, above the list (30-66%), the CTA (42-54%) and the captions. One line, up to 30 characters.
export type ImpactItem = {text: string; from: number; dur: number};

export type ImpactCaptionProps = {
  width: number;
  height: number;
  fps: number;
  items: ImpactItem[];
  duration: number; // seconds, from the first item to the end of the last
};

export const IMPACT_CENTER = 0.22;
export const IMPACT_HEIGHT = 0.12;

export const ImpactCaption: React.FC<ImpactCaptionProps> = ({items}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const unit = Math.min(width, height) / 100;
  const item = items.find((i) => frame >= i.from && frame < i.from + i.dur);
  const text = item ? item.text.toUpperCase() : '';
  const fontSize = Math.min(14 * unit, (width - 20 * unit) / (1.0 * Math.max(1, text.length)));
  return (
    <AbsoluteFill style={{backgroundColor: '#000000'}}>
      {item ? (
        <div
          style={{
            position: 'absolute',
            top: height * (IMPACT_CENTER - IMPACT_HEIGHT / 2),
            height: height * IMPACT_HEIGHT,
            left: 0,
            right: 0,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontFamily: 'Helvetica, Arial, sans-serif',
            fontWeight: 800,
            fontSize,
            color: '#ffffff',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
          }}
        >
          {text}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
