"""
Extracts unique still images from a video file.

Usage:
  extract-slides.py <video_file> [-s <sample_fps>] [-c <corr>]
  extract-slides.py (-h | --help)
  extract-slides.py (-v | --version)

Options:
  -s <sample_fps>   the frequency with which to sample video frames to check for changes [default: 1.0]
  -c <corr>         the correlation threshold above which two frames are considered the same [default: 0.999]
  -h --help         print help
  -v --version      print version
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import timedelta
from functools import partial
from itertools import chain, count, pairwise, takewhile
from operator import not_
from pathlib import Path
from typing import Any, Callable, Iterator, NamedTuple, Optional, Tuple, Type, TypeVar

import cv2 as cv
from docopt import docopt
from more_itertools import first, last, split_when
from numpy import set_printoptions
from numpy.typing import NDArray
from single_source import get_version
from tqdm import tqdm


Image = NDArray


FrameMatcher = Callable[["Frame", "Frame"], bool]


def frames_match(correlation_threshold: float, frame1: Frame, frame2: Frame) -> bool:
    match: NDArray = cv.matchTemplate(frame1.image, frame2.image, method=cv.TM_CCORR_NORMED)
    return (match > correlation_threshold).all() # type: ignore


@dataclass
class VideoSlideExtractor:
    path: Path
    sample_frames_per_second: float
    frame_matcher: FrameMatcher
    _capture: cv.VideoCapture = field(init=False)

    def __post_init__(self):
        self._capture = cv.VideoCapture(str(self.path))

    def current_frame(self) -> Frame:
        success, image = self._capture.retrieve()
        assert success
        timestamp_ms = self._capture.get(cv.CAP_PROP_POS_MSEC)
        timestamp = timedelta(milliseconds=timestamp_ms)
        return Frame(image=image, timestamp=timestamp, source=self.path)

    def frames(self) -> Iterator[Frame]:
        video_frames_per_second: float = self._capture.get(cv.CAP_PROP_FPS)
        frame_step: int = int(video_frames_per_second / self.sample_frames_per_second)
        for fnum in count():
            if not self._capture.grab():
                break
            if fnum % frame_step == 0:
                yield self.current_frame()

    def frame_runs(self) -> Iterator[list[Frame]]:
        return split_when(self.frames(), lambda *a: not self.frame_matcher(*a))

    def slides(self) -> Iterator[Slide]:
        return (
            Slide(first(frame_run), last(frame_run)) for frame_run in self.frame_runs()
        )


@dataclass
class Frame:
    image: Image
    timestamp: timedelta
    source: Path


@dataclass
class Slide:
    start: Frame
    end: Frame

    def outpath(self) -> Path:
        source = self.start.source
        return Path(source.parent, f"{source.stem}__{self.start.timestamp}.png")

    def outimage(self) -> Image:
        return self.end.image

    def write(self):
        assert cv.imwrite(str(self.outpath()), self.outimage())


if __name__ == "__main__":
    set_printoptions(edgeitems=0)

    version: str = get_version(__name__, Path(__file__).parent) or ""
    args: dict[str, Any] = docopt(str(__doc__), version=version)

    matcher = partial(frames_match, float(args["-c"]))
    extractor = VideoSlideExtractor(
        Path(args["<video_file>"]), float(args["-s"]), matcher
    )

    for slide in tqdm(extractor.slides()):
        slide.write()
