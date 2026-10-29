## Why

mediaComp (a community fork of JES4py) no longer has the JES movie functions. They were removed in commit `98e1a56` (v0.4.11), and the copies that existed before that never worked: every function crashed on undefined names or Java leftovers. Students using mediaComp on Windows with Thonny currently have no way to build, play or save animations, and `src/mediaComp/__init__.pyi` still advertises the missing functions to editors. The course needs working movie support now, delivered in a way that can later be contributed back upstream.

## What Changes

- Add a single student-facing module, `mediaCompMovie.py`, that students put next to their scripts and import with `from mediaCompMovie import *` after `from mediaComp import *`. It works with the stock PyPI mediaComp (>= 0.4.15) and uses only mediaComp's public API plus Pillow, numpy and pygame-ce, which mediaComp already installs.
- The module is laid out in three parts so it can later be split into the package: a `Movie` class (future `models/Movie.py`), JES-style wrapper functions (future `core/movie.py`), and a pygame player entry point (future `scripts/moviePlayer.py`).
- Support both the textbook JES movie API (`makeMovie`, `makeMovieFromInitialFile`, `addFrameToMovie`, `writeFramesToDirectory`, `playMovie`, `writeAVI`, `writeQuicktime`) and Mark Guzdial's notebook API (`makeMovie(directory)`, `writeFrame`, `playMovie(movie, delay)`).
- Add video export to MP4, AVI and MOV (`writeMovie`, `writeMP4`, `writeAVI`, `writeQuicktime`) through `imageio` + `imageio-ffmpeg`. These are optional and imported only when exporting. If they are missing, the student sees a clear install hint, and playback still works.
- Add playback in a pygame window run as a subprocess. It loops until the window is closed and blocks the calling script by default. A module-level default and a per-call keyword make it non-blocking.
- Add a pytest suite split by platform: portable tests that run in WSL/Linux and in CI, Windows-only tests that are skipped elsewhere, and a manual Windows + Thonny checklist.
- Work around an upstream bug: `makePicture` and `writePictureTo` in mediaComp refer to a global `mediaFolder` that is never assigned, so relative paths are expected to raise `NameError`. The movie code resolves paths itself and passes absolute paths to mediaComp. The bug itself is recorded as a known issue and is not fixed in this change.
- Out of scope: changes to the mediaComp package (Phase 2, a later change), animated GIF export, the JES `explore(movie)` / FrameSequencer GUI, Colab/notebook display, and turtles.

## Capabilities

### New Capabilities
- `movie-frames`: The `Movie` object and how frames get into and out of it: creating movies in both API styles, loading frame sequences from files, adding frames, writing numbered frame images, and path resolution.
- `movie-playback`: Playing a movie in a window: frame rate and delay, looping, blocking versus non-blocking behaviour, player controls, and clean shutdown.
- `movie-export`: Writing a movie to MP4, AVI or MOV: format selection, the default format, frame validation and normalisation, and behaviour when the optional export dependencies are missing.

### Modified Capabilities
<!-- None: there are no existing specs in this project. -->

## Impact

- **New files:** `mediaCompMovie.py` (location decided in design), a `tests/` layout with a shared `conftest.py`, `tests/movie/` and `tests/windows/`, and a manual test checklist.
- **Existing package code:** not changed. `__init__.pyi`, `core/image.py` and `core/sound.py` are left as they are; Phase 2 updates them.
- **Dependencies:** no new runtime dependencies for playback. Export needs `imageio` and `imageio-ffmpeg`, installed by the student when wanted. Development adds `pytest`, `imageio` and `imageio-ffmpeg` to the local venv.
- **CI:** the existing `tests.yaml` workflow (pytest on `windows-latest`, Python 3.10–3.14) runs the new suite. It triggers only on pushes and PRs to `master`.
- **Students:** add one import line to their scripts. Existing mediaComp code is unaffected.
- **Later upstream contribution (Phase 2):** split the module into the package, update `__init__.py`, `__init__.pyi` and `pyproject.toml` (an optional `movie` extra), open an issue upstream first, and report the `mediaFolder` bug separately.
