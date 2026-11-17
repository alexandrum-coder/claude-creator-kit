import React from 'react';
import {Composition} from 'remotion';
import {Intro, IntroProps} from './Intro';
import {ChapterTitle, ChapterTitleProps} from './ChapterTitle';
import {ListOverlay, ListOverlayProps} from './ListOverlay';
import {MotionBlurDissolve, MotionBlurDissolveProps, MOTION_BLUR_DISSOLVE_SEC} from './MotionBlurDissolve';
import {TitlePop, TitlePopProps, TITLE_POP_FADE_FRAMES, TITLE_POP_HOLD_SEC} from './TitlePop';
import {NumberedList, NumberedListProps} from './NumberedList';
import {CtaKeyword, CtaKeywordProps} from './CtaKeyword';
import {ImpactCaption, ImpactCaptionProps} from './ImpactCaption';

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
    <Composition
      id="TitlePop"
      component={TitlePop as React.FC<any>}
      durationInFrames={Math.round(TITLE_POP_HOLD_SEC * 30) + TITLE_POP_FADE_FRAMES}
      {...base}
      defaultProps={{width: 1920, height: 1080, fps: 30, text: 'Titlu'} satisfies TitlePopProps}
      calculateMetadata={({props}: {props: Record<string, any>}) => ({
        durationInFrames: Math.round((props.hold ?? TITLE_POP_HOLD_SEC) * props.fps) + TITLE_POP_FADE_FRAMES,
        width: props.width,
        height: props.height,
        fps: props.fps,
      })}
    />
    <Composition
      id="MotionBlurDissolve"
      component={MotionBlurDissolve as React.FC<any>}
      durationInFrames={43}
      width={1920}
      height={1080}
      fps={25}
      defaultProps={{width: 1920, height: 1080, fps: 25, a: 'a.mp4', b: 'b.mp4'} satisfies MotionBlurDissolveProps}
      calculateMetadata={({props}: {props: Record<string, any>}) => ({
        durationInFrames: Math.round(MOTION_BLUR_DISSOLVE_SEC * props.fps),
        width: props.width,
        height: props.height,
        fps: props.fps,
      })}
    />
    <Composition
      id="NumberedList"
      component={NumberedList as React.FC<any>}
      durationInFrames={5 * 30}
      width={1080}
      height={1920}
      fps={30}
      defaultProps={{width: 1080, height: 1920, fps: 30, colors, duration: 5,
        items: [{text: 'Primul punct', at: 0}, {text: 'Al doilea punct', at: 1}]} satisfies NumberedListProps}
      calculateMetadata={({props}: {props: Record<string, any>}) => ({
        durationInFrames: Math.max(1, Math.round(props.duration * props.fps)),
        width: props.width,
        height: props.height,
        fps: props.fps,
      })}
    />
    <Composition
      id="CtaKeyword"
      component={CtaKeyword as React.FC<any>}
      durationInFrames={3 * 30}
      width={1080}
      height={1920}
      fps={30}
      defaultProps={{width: 1080, height: 1920, fps: 30, colors, word: 'Postura', duration: 3} satisfies CtaKeywordProps}
      calculateMetadata={({props}: {props: Record<string, any>}) => ({
        durationInFrames: Math.max(1, Math.round(props.duration * props.fps)),
        width: props.width,
        height: props.height,
        fps: props.fps,
      })}
    />
    <Composition
      id="ImpactCaption"
      component={ImpactCaption as React.FC<any>}
      durationInFrames={30}
      width={1080}
      height={1920}
      fps={30}
      defaultProps={{width: 1080, height: 1920, fps: 30, items: [{text: 'Stop', from: 0, dur: 30}],
        duration: 1} satisfies ImpactCaptionProps}
      calculateMetadata={({props}: {props: Record<string, any>}) => ({
        durationInFrames: Math.max(1, Math.round(props.duration * props.fps)),
        width: props.width,
        height: props.height,
        fps: props.fps,
      })}
    />
  </>
);
