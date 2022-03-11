# video-slide-extractor

Finds runs of consecutive similar frames from a video file, and exports first and/or last frames from each run as
images. Useful for e.g. extracting slides from a recorded presentation.

Lists exported image file paths on stdout.


Usage:
  slide-extractor <video_file> [-b <beg_outfmt>] [-e <end_outfmt>] [-s <sample_rate> | -n <num_samples>] [-c <corr>] [-d | --debug]
  slide-extractor (-h | --help)
  slide-extractor (-v | --version)


OPTIONS:

  -b, --begfmt <string>
                    OUTFILE FORMAT STRING to determine filename for first frame in each run [default: none]

  -e, --endfmt <string>
                    OUTFILE FORMAT STRING to determine filename for last frame in each run [default: %f__%t.png]

  -s, --sample-rate ( <float|int>fps | <float|int>% )
                    approximate frequency with which to sample video frames to check for changes. must be suffixed with
                    "fps" or "%". an fps value is divided into the source video's native framerate in FPS to determine #
                    frames to skip each iteration. a percentage value is interpreted as a percentage of the source
                    video's native framerate and handled similarly. [default: 1.0fps]

  -c, --correlation-threshold <float>
                    correlation threshold above which two frames are considered the same [default: 0.999]

  -d, --debug       drop into an ipdb debugger for every run found; requires installing [debug] extra
  -h, --help        print help
  -v, --version     print version


OUTFILE FORMAT STRINGS:
  %%              Literal percent sign
  %f              Path to input video file, but without its extension
  %d              Path to directory containing the input video file
  %[W]n           Index of the extracted run, starting from 0, with optional pad width (e.g. %2n)
  %[W]N           Index of the extracted run, starting from 1, with optional pad width
  %t    / %T      Timestamp of first/last frame, in timedelta format (H:MM:SS)
  %[W]s / %[W]S   Timestamp of first/last frame, in seconds since start, w/ optional pad width
  %[W]m / %[W]M   Timestamp of first/last frame, in ms since start, w/ optional pad width
  %[W]i / %[W]I   Frame number of first/last frame, with optional pad width


Inspired by https://github.com/szanni/slideextract.
