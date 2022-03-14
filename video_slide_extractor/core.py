from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from functools import cached_property
from pathlib import Path
from typing import Callable, Iterator, Optional, Protocol, Type, TypeAlias

import cv2 as cv
from more_itertools import first, last, side_effect, split_when
from numpy.typing import NDArray
from tqdm import tqdm

Image: TypeAlias = NDArray


FrameMatcher = Callable[["Frame", "Frame"], bool]


def frames_match(correlation_threshold: float, frame1: Frame, frame2: Frame) -> bool:
    match = cv.matchTemplate(frame1.image, frame2.image, method=cv.TM_CCORR_NORMED)
    return (match > correlation_threshold).all()  # type: ignore


class ProgressUpdater(Protocol):
    def __init__(self, unit: str, total: Optional[int] = None):
        ...

    def update(self, n: int = 1):
        ...


@dataclass
class VideoSlideExtractor:
    path: Path
    sample_rate: str
    frame_matcher: FrameMatcher
    progress: Type[ProgressUpdater] = tqdm  # type: ignore
    _capture: cv.VideoCapture = field(init=False)

    def __post_init__(self):
        self._capture = cv.VideoCapture(str(self.path))

    def frame_rate(self) -> int:
        return self._capture.get(cv.CAP_PROP_FPS)

    @cached_property
    def frame_sample_period(self) -> int:
        if self.sample_rate and self.sample_rate.endswith("fps"):
            return int(self.frame_rate() / float(self.sample_rate[:-3]))
        elif self.sample_rate and self.sample_rate.endswith("%"):
            return int(self.frame_rate() * float(self.sample_rate[:-1]))
        else:
            return int(self.total_frames() / (int(self.sample_rate) - 1))

    def current_frame(self) -> Frame:
        success, image = self._capture.retrieve()
        assert success
        return Frame(
            image=image,
            fnum=self.current_frame_num(),
            timestamp=self.current_timestamp(),
            source=self.path,
        )

    def current_frame_num(self) -> int:
        return self._capture.get(cv.CAP_PROP_POS_FRAMES)

    def total_frames(self) -> int:
        return self._capture.get(cv.CAP_PROP_FRAME_COUNT)

    def current_timestamp(self) -> timedelta:
        return timedelta(milliseconds=self._capture.get(cv.CAP_PROP_POS_MSEC))

    def frames(self) -> Iterator[Frame]:
        fnum = 0
        progress = self.progress(unit=" frames", total=self.total_frames())
        while self._capture.grab():
            if fnum % self.frame_sample_period == 0:
                yield self.current_frame()
            fnum += 1
            progress.update()

    def frame_runs(self) -> Iterator[list[Frame]]:
        return split_when(self.frames(), lambda *a: not self.frame_matcher(*a))

    def slides(self) -> Iterator[Slide]:
        progress = self.progress(unit=" slides")
        return side_effect(
            lambda _: progress.update(),
            (
                Slide(i, first(frame_run), last(frame_run))
                for i, frame_run in enumerate(self.frame_runs())
            ),
        )


@dataclass
class Frame:
    image: Image
    fnum: int
    timestamp: timedelta
    source: Path


@dataclass
class Slide:
    index: int
    start: Frame
    end: Frame

    @property
    def index0(self) -> int:
        return self.index - 1

    @cached_property
    def source(self) -> Path:
        assert self.start.source == self.end.source
        return self.start.source
