"""
Extracts unique still images from a video file.

Usage:
  extract-slides.py <video_file> [-o <outformat>] [-f <sample_fps>] [-c <corr>]
  extract-slides.py (-h | --help)
  extract-slides.py (-v | --version)

Options:
  -o <outformat>    specify a format string to use as output file basename for extracted images [default: %f-%t]
  -f <sample_fps>   the frequency with which to sample video frames to check for changes [default: 1.0]
  -c <corr>         the correlation threshold above which two frames are considered the same [default: 0.999]
  -h --help         print help
  -v --version      print version

Outformat String Placeholders:
  %f  basename of the input video file
  %t  timestamp of the extracted image
  %%  literal percent sign
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from itertools import chain, count, pairwise, takewhile
from operator import not_
from pathlib import Path
from typing import Any, Callable, Iterator, NamedTuple, Optional, Tuple, Type, TypeVar

from cv2 import CAP_PROP_FPS, CAP_PROP_POS_MSEC, TM_CCORR_NORMED, VideoCapture, matchTemplate, minMaxLoc
from docopt import docopt
from more_itertools import first, last, split_when
from numpy import set_printoptions
from numpy.typing import NDArray
from single_source import get_version
from tqdm import tqdm


Image = NDArray


@dataclass
class Frame:
    image: Image
    timestamp: timedelta
    video: VideoCapture

    @classmethod
    def from_video_state(cls: Type[Frame], video: VideoCapture) -> Optional[Frame]:
        success, image = video.retrieve()
        if success:
            return cls(
                video=video,
                image=image,
                timestamp=timedelta(milliseconds=video.get(CAP_PROP_POS_MSEC)),
            )


@dataclass
class Slide:
    frame_start: Frame
    frame_end: Frame

    def persist(self: Slide)]


def frames_from(video_file: Path, sample_frames_per_second: float = 1.0) -> Iterator[Frame]:
    video: VideoCapture = VideoCapture(video_file)
    video_frames_per_second: float = video.get(CAP_PROP_FPS)
    frame_step: int = int(video_frames_per_second / sample_frames_per_second)
    return (
        frame
        for fnum in count()
        if video.grab()
        if fnum % frame_step == 0
        if (frame := Frame.from_video_state(video))
    )



def frames_match(frame1: Frame, frame2: Frame, correlation_threshold: float = 0.999) -> bool:
    tmpl_match = matchTemplate(frame1.image, frame2.image, method = TM_CCORR_NORMED)
    min, _max, _minLoc, _maxLoc = minMaxLoc(tmpl_match)
    return min < correlation_threshold


FrameMatcher=Callable[[Frame, Frame], bool]


def slides_from(frames: Iterator[Frame], frames_match: FrameMatcher = frames_match) -> Iterator[Slide]:
    return (
        Slide(first(matching_frames), last(matching_frames))
        for matching_frames in split_when(frames, lambda *a: not frames_match(*a))
    )


if __name__ == "__main__":
    set_printoptions(edgeitems = 0)

    version: str = get_version(__name__, Path(__file__).parent) or ''
    args: dict[str, Any] = docopt(str(__doc__), version = version)

    _frames=frames_from(args['<video_file>'], float(args['-f']))
    _frames_match=partial(frames_match, correlation_threshold = float(args['-c']))
    _slides=slides_from(_frames, frames_match = _frames_match)

    for slide in tqdm(_slides):
        import ipdb; ipdb.set_trace()
