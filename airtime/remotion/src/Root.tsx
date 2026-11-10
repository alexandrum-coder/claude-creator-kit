import React from 'react';
import {Composition} from 'remotion';
import {Intro, IntroProps} from './Intro';
import {ChapterTitle, ChapterTitleProps} from './ChapterTitle';
import {ListOverlay, ListOverlayProps} from './ListOverlay';

const colors = {primary: '#14213d', accent: '#fca311'};
const base = {width: 1920, height: 1080, fps: 30, colors};

// Durations are fixed by the spec; render.mjs overrides width, height, fps and colors per run.
export const Root: React.FC = () => (
  <>
    <Composition
      id="Intro"
      component={Intro as React.FC<any>}
      durationInFrames={4 * 30}
      {...base}
      defaultProps={{...base, title: 'Titlu', channel: 'Canal', durationSec: 4} satisfies IntroProps}
      calculateMetadata={({props}: {props: Record<string, any>}) => ({
        durationInFrames: Math.round((props as IntroProps).durationSec * props.fps),
        width: props.width,
        height: props.height,
        fps: props.fps,
      })}
    />
    <Composition
      id="ChapterTitle"
      component={ChapterTitle as React.FC<any>}
      durationInFrames={3 * 30}
      {...base}
      defaultProps={{...base, text: 'Capitol'} satisfies ChapterTitleProps}
      calculateMetadata={({props}: {props: Record<string, any>}) => ({
        durationInFrames: 3 * props.fps,
        width: props.width,
        height: props.height,
        fps: props.fps,
      })}
    />
    <Composition
      id="ListOverlay"
      component={ListOverlay as React.FC<any>}
      durationInFrames={5 * 30}
      {...base}
      defaultProps={{...base, items: ['Primul punct', 'Al doilea punct']} satisfies ListOverlayProps}
      calculateMetadata={({props}: {props: Record<string, any>}) => ({
        durationInFrames: 5 * props.fps,
        width: props.width,
        height: props.height,
        fps: props.fps,
      })}
    />
  </>
);
