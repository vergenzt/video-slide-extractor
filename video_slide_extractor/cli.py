"""
# video-slide-extractor

Finds runs of consecutive similar frames from a video file, and exports first and/or
last frames from each run as images. Useful for e.g. extracting slides from a recorded
presentation.

Lists exported image file paths on stdout.


Usage:
  {program} <video_file>
            [-b <beg_outfmt>] [-e <end_outfmt>]
            [-s <sample_rate>] [-c <corr>]
            [-d | --debug]

  {program} (-h | --help)
  {program} (-v | --version)


OPTIONS:

  -b, --begfmt <string>
        OUTFILE FORMAT STRING to determine filename for first frame in each run
        [default: none]

  -e, --endfmt <string>
        OUTFILE FORMAT STRING to determine filename for last frame in each run
        [default: %f__%t.png]

  -s, --sample-rate ( <float|int>fps | <float|int>% )
        approximate frequency with which to sample video frames to check for changes.
        must be suffixed with "fps" or "%". an fps value is divided into the source
        video's native framerate in FPS to determine # frames to skip each iteration. a
        percentage value is interpreted as a percentage of the source video's native
        framerate and handled similarly. [default: 1.0fps]

  -c, --correlation-threshold <float>
        correlation threshold above which two frames are considered the same
        [default: 0.999]

  -d, --debug
        drop into an ipdb debugger for every run found; requires [debug] extra

  -h, --help
        print help

  -v, --version
        print version


{outfile_format_docs}


Inspired by https://github.com/szanni/slideextract.
"""

from functools import partial
from pathlib import Path
from sys import argv
from typing import Any

import cv2 as cv
import numpy as np
from docopt import docopt
from single_source import get_version
from tqdm import tqdm

from .core import VideoSlideExtractor, frames_match
from .output_path_format import OutputPathFormatter
from .output_path_format import __doc__ as outfile_format_docs


def main():
    version: str = str(get_version(__name__, Path(__file__).parent))
    program: str = Path(argv[0]).name
    doc: str = str(__doc__).format(
        program=program, outfile_format_docs=str(outfile_format_docs).strip()
    )
    args: dict[str, Any] = docopt(doc=doc, version=version)

    matcher = partial(frames_match, float(args["--correlation-threshold"]))
    extractor = VideoSlideExtractor(
        Path(args["<video_file>"]), args["--sample-rate"], matcher
    )

    progress = tqdm(total=int(extractor.total_frames()), unit=" frames")
    extractor._on_update = progress.update

    for slide in extractor.slides():
        if args["--debug"]:
            np.set_printoptions(edgeitems=0)
            import ipdb  # fmt: skip
            ipdb.set_trace()

        images = {"--begfmt": slide.start.image, "--endfmt": slide.end.image}
        for argname, image in images.items():
            if (outfmt := args[argname]) and outfmt != "none":
                fmter = OutputPathFormatter(slide, outfmt)
                path = fmter.output_path()
                progress.clear()
                print(path)
                progress.refresh()
                cv.imwrite(str(path), image)

    progress.close()


if __name__ == "__main__":
    main()
