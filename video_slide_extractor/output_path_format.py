"""
OUTFILE FORMAT STRINGS:
  %%              Literal percent sign
  %f              Path to input video file, but without its extension
  %d              Path to directory containing the input video file
  %[W]n           Index of the extracted run, starting from 0
  %[W]N           Index of the extracted run, starting from 1
  %t    / %T      Timestamp of first/last frame, in timedelta format (H:MM:SS)
  %[W]s / %[W]S   Timestamp of first/last frame, in seconds since start
  %[W]m / %[W]M   Timestamp of first/last frame, in ms since start
  %[W]i / %[W]I   Frame number of first/last frame, with optional pad width

[W] above indicates an optional numeric width to zero-pad the attribute to.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict

from .core import Slide


@dataclass
class Fmter:
    attr: Callable[[Slide], Any]
    widthable: bool = False


TAGS: Dict[str, Fmter] = dict(
    # can't use % as kwarg, so put it separately
    [("%", Fmter(lambda _: "%"))],
    # use kwargs for the rest so Python can catch duplicates
    # (https://stackoverflow.com/a/22242922)
    f=Fmter(lambda s: s.source),
    d=Fmter(lambda s: s.source.parent),
    n=Fmter(lambda s: s.index, True),
    N=Fmter(lambda s: s.index0, True),
    t=Fmter(lambda s: s.start.timestamp),
    s=Fmter(lambda s: s.start.timestamp.total_seconds(), True),
    m=Fmter(lambda s: s.start.timestamp.total_seconds() * 1000, True),
    i=Fmter(lambda s: s.start.fnum, True),
    T=Fmter(lambda s: s.end.timestamp),
    S=Fmter(lambda s: s.end.timestamp.total_seconds(), True),
    M=Fmter(lambda s: s.end.timestamp.total_seconds() * 1000, True),
    I=Fmter(lambda s: s.end.fnum, True),
)


@dataclass
class OutputPathFormatter:
    slide: Slide
    outfmt: str

    _OUTFMT_RE: ClassVar[re.Pattern] = re.compile(
        r"""
            (?<!%)          # can't be preceded by a % sign
            %               # literal % to start the format tag
            (?P<width>\d*)  # optional width qualifier (ignored if not applicable)
            (?P<char>.)     # match any character so we can complain about unescaped
                            # percents or bad tags
        """,
        re.VERBOSE,
    )

    def _outfmt_repl(self, match: re.Match) -> Any:
        width, char = match.groups()
        tag = TAGS[char]
        out = str(tag.attr(self.slide))
        if tag.widthable and width:
            out = out.zfill(int(width))
        return out

    def output_path(self) -> Path:
        return self._OUTFMT_RE.sub(self._outfmt_repl, self.outfmt)
