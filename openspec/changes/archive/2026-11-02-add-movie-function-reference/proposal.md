## Why

Students learn mediaComp from `Documentation/Media Functions.pdf`, a reference that gives each function's signature, a short description, its parameters and return value, and a small example. The movie functions in `contrib/movie/mediaCompMovie.py` have no equivalent: only docstrings and a summary table in the README. The handout is needed now for the course, and the same text should later be usable in an upstream pull request.

Writing that reference also showed that `playMovie` is the only function a student would need keyword arguments for (`framesPerSec=`, `block=`). Neither JES nor mediaComp uses keyword arguments in anything students see: optional parameters are trailing positionals shown in `[ ]`, as in `play(sound[, isBlocking])`. In JES, `playMovie(movie)` had no speed parameter at all; the frame rate was chosen only when writing a video file. Simplifying `playMovie` to match removes one hurdle for students and gives the reference one consistent style.

## What Changes

- **BREAKING** `playMovie(movie[, isBlocking])` replaces `playMovie(movie, delay=None, framesPerSec=None, block=None)`.
  - Playback always runs at 16 frames per second, the JES default. The `delay` and `framesPerSec` parameters are removed.
  - `isBlocking` is an optional positional argument that defaults to `False`, matching mediaComp's `play(sound[, isBlocking])`. Like `play`, it is read for truthiness and is not validated.
  - The `block` keyword is removed.
- **BREAKING** `setPlayBlocking`, `getPlayBlocking` and the `DEFAULT_PLAY_BLOCKING` module global are removed. The public API goes from 14 to 12 names.
- The frame rate is chosen only when saving, through the existing optional positional `framesPerSec` of `writeMovie`, `writeMP4`, `writeAVI` and `writeQuicktime`. These functions do not change.
- Add a student function reference for the movie functions:
  - **Source:** a single Markdown file in `contrib/movie/docs/`, written in a strict entry format that mirrors the upstream document (signature heading, description, parameter and `returns:` lines, example, explanation).
  - **Build:** a script turns it into `Movie Functions.docx` using upstream's style names (Heading 1/2/3, `Program code`, italic parameter names). LibreOffice then converts the `.docx` to `Movie Functions.pdf`.
  - **Delivery:** both generated files are committed next to `mediaCompMovie.py`.
  - **Content:**
    - a "Movie Functions" section with a short preamble covering setup, frame file naming, where relative paths go, and the optional export packages
    - one entry per public function, written in the upstream style
    - an appendix of differences from the JES movie functions
  - **Drift test:** every name in `__all__` has exactly one entry, and each entry's signature matches the function's real parameters.
- Shorten the README's function table to a list that points to the PDF. Update its examples, the manual Windows checklist and the tests for the new `playMovie` signature.
- Out of scope:
  - Inserting the section into upstream's `Media Functions.docx`; how upstream wants documentation is not yet known.
  - Exact font fidelity with upstream's Word-made PDF. The generated `.docx` can be restyled by hand.
  - Speed-control keys in the player, recorded as future work.
  - Changes to the mediaComp package itself.

## Capabilities

### New Capabilities
- `movie-reference-doc`: The student function reference for the movie functions: its single Markdown source and entry format, the generated `.docx` and `.pdf`, the content it must cover, and the check that keeps it in step with the code.

### Modified Capabilities
- `movie-playback`: Playback speed becomes a fixed 16 frames per second with no speed arguments. Blocking becomes an optional positional `isBlocking` that defaults to `False`, as in `play()`. The `block` keyword, `setPlayBlocking`, `getPlayBlocking` and `DEFAULT_PLAY_BLOCKING` are removed.

## Impact

- **Code:** `contrib/movie/mediaCompMovie.py`: `playMovie`, `__all__`, and the removal of the blocking setting and its setter and getter. The player subprocess and the export code are unchanged.
- **Tests:**
  - `tests/movie/test_playback.py`, `tests/movie/test_public_names.py` and `tests/windows/test_player_win.py` change for the new signature and the removed names.
  - `tests/windows/MANUAL_CHECKLIST.md` changes the same way.
  - A new drift test checks the reference source against the code.
- **New files:**
  - `contrib/movie/docs/` holds the Markdown source and the build script.
  - `contrib/movie/Movie Functions.docx` and `contrib/movie/Movie Functions.pdf` are generated and committed.
- **Dependencies:**
  - `python-docx` is added to `contrib/movie/requirements-dev.txt` for the build only. Students never need it.
  - LibreOffice and fonts (Arial and Courier New from the Microsoft core fonts, Carlito and Caladea in place of Calibri and Cambria) are installed with apt in the WSL development environment to make the PDF.
- **Students:** scripts that call `playMovie(movie, 0.1)`, `framesPerSec=`, `block=` or `setPlayBlocking` must change.
  - A positional second argument such as `0.1` is now read as `isBlocking`, so it makes the call block rather than raising an error.
  - Default behaviour changes from blocking to non-blocking. In Thonny the window keeps playing after the script ends.
  - The movie functions have not yet been handed to students, so this is the cheapest time to make the change.
- **Upstream (later):** the Markdown source and generated `.docx` are the starting point for the documentation part of the eventual mediaComp pull request. Small errors found in upstream's PDF go into the same upstream issue as the `mediaFolder` bug.
