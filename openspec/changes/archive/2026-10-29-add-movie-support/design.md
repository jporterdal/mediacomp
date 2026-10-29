## Context

See proposal.md for motivation and specs/ for the required behaviour. This section covers only what shapes the implementation.

- The code is developed on the `movies` branch of `jporterdal/mediacomp`, a standalone copy of `dllargent/mediaComp` at v0.4.15. `master` mirrors upstream and is never committed to. A later change (Phase 2) splits the code into the package and contributes it upstream.
- Students run Windows and Thonny, with mediaComp installed from PyPI into Thonny's interpreter. Development and most testing happen in WSL2 using the repo's `venv`, which has mediaComp installed in editable mode. Windows-specific testing is done by hand on the Windows host.
- What mediaComp provides:
  - `Picture.getImage()` returns the underlying PIL image.
  - `Picture.show()` already starts a helper script (`scripts/show.py`) as a subprocess with `sys.executable`, which is a working precedent for the player.
  - Pillow, numpy, pygame-ce and wxPython are already installed with mediaComp.
- `ConfigManager` (`models/Config.py`) reads and writes `~/.mediaCompConfig` when mediaComp is imported. Its media path defaults to `""`, so `getMediaFolder(name)` returns `name`, a path relative to the current directory.
- Upstream bug: `makePicture` and `writePictureTo` (`core/image.py`) and `makeSound`/`writeSoundTo` (`core/sound.py`) declare `global mediaFolder` and add it to relative paths, but nothing assigns `mediaFolder`. Confirmed by running mediaComp 0.4.15 in a fresh temp directory: `makePicture('x.png')` and `writePictureTo(p, 'y.png')` raise `NameError: name 'mediaFolder' is not defined` for any relative path. This happens whether or not the file exists and whether or not a media folder has been set with `setMediaFolder`. Absolute paths work. The movie code works around it (see D3), and fixing it is out of scope.
- The existing CI workflow runs `pytest` on `windows-latest` for Python 3.10–3.14, with only `pytest` and mediaComp installed. It triggers on pushes and PRs to `master` only.

## Goals / Non-Goals

**Goals:**
- One file, `mediaCompMovie.py`, that works with an unmodified PyPI mediaComp >= 0.4.15 on Python >= 3.10.
- Internal sections that match the future package files, so Phase 2 is a mechanical split.
- A test suite most of which runs headless in WSL, with Windows-only tests isolated and runnable on their own.

**Non-Goals:**
- Changing anything under `src/mediaComp/` or `pyproject.toml`; that is Phase 2.
- Fixing the `mediaFolder` bug.
- Changing `.github/workflows/` on this branch, because those commits would have to be left out of an upstream PR.
- Supporting macOS or Linux as student platforms. The code stays portable because tests run on Linux, but only Windows is checked by hand.

## Decisions

### D1. File layout
```
contrib/movie/
  mediaCompMovie.py        the student file (sections A/B/C below)
  README.md                student instructions and function reference
  requirements-dev.txt     pytest, imageio, imageio-ffmpeg
tests/
  conftest.py              config isolation, marker registration, Windows auto-skip
  movie/                   portable tests (WSL, Linux, Windows, CI)
  windows/                 Windows-only tests, marked `windows`
  windows/MANUAL_CHECKLIST.md   manual Windows + Thonny checks
```
`contrib/movie/` keeps everything students receive in one folder, away from `src/`, and is easy to leave out of the Phase 2 PR. `tests/` is the repo's existing pytest location and is already what CI collects. The existing `tests/Picture_test.py` is left as it is.

Alternative considered: putting the file at the repo root. It is simpler to find, but mixes student deliverables with project files.

### D2. Structure of `mediaCompMovie.py`
The file has three clearly marked sections, each mapping to one Phase 2 file:
- **Section A, `Movie` (→ `models/Movie.py`):**
  - Attributes: `frames` (a list where each entry is an absolute path `str` or a PIL `Image` snapshot) and `dir` (`str` or `None`).
  - Methods: `addFrame`, `__len__`, `__getitem__` and `__str__`.
  - `resolvedFrames()` returns `frames` if non-empty, otherwise scans `dir` (spec: "Frames come from the directory when none were added").
  - Frame-loading helpers: `_loadImage(entry) -> PIL.Image` and numeric sort.
- **Section B, wrapper functions (→ `core/movie.py`):** `makeMovie`, `makeMovieFromInitialFile`, `addFrameToMovie`, `writeFrame`, `writeFramesToDirectory`, `playMovie`, `writeMovie`, `writeMP4`, `writeAVI`, `writeQuicktime`, and the setters and getters. Each one validates, prints the message and raises `ValueError`, following mediaComp's convention.
- **Section C, player (→ `scripts/moviePlayer.py`):** `_runPlayer(manifest)`, reached through `if __name__ == "__main__":` with `--play <manifest.json>`.

The file imports only mediaComp's public names (`Picture`, `getMediaFolder`) plus the standard library, PIL and numpy at the top level. pygame is imported only inside section C, and imageio only inside export. That way, importing the module never opens a pygame window or prints pygame's banner, and still works without imageio.

`__all__` lists exactly the student-facing functions, so `from mediaCompMovie import *` does not leak helpers or overwrite mediaComp names.

### D3. Path resolution and the `mediaFolder` workaround
`_resolve(path)` returns `path` unchanged if it is absolute. Otherwise it returns `os.path.abspath(getMediaFolder(path))`, which falls back to the current directory when no media folder is set. Every file the movie code reads or writes goes through `_resolve`, and is read and written with PIL directly (`Image.open`, `Image.save`) rather than through `makePicture`/`writePictureTo`, so the bug can never be reached. `writeFramesToDirectory` with no directory uses `os.getcwd()` explicitly, as required by the spec.

Alternative considered: calling `writePictureTo` with absolute paths. That also avoids the bug, but adds nothing over `picture.getImage().save(...)` and ties frame writing to a function that is known to be broken.

### D4. Picture frames are stored as PIL snapshots in memory
`addFrameToMovie(picture, movie)` stores `picture.getImage().copy()`. This satisfies the snapshot requirement and keeps the common "draw on one canvas, add it each loop" pattern correct. Memory cost is about 0.9 MB per 640x480 frame, so 100 frames take about 90 MB, which is acceptable for classroom-sized animations.

Alternative considered: writing each snapshot to a temp PNG as it is added. That uses less memory, but leaves temp files to manage over the movie's lifetime, with no clear owner for removing them.

### D5. Frame discovery and ordering
- Directory scans keep files whose lowercased extension is one of `.png`, `.jpg` or `.jpeg`.
- `makeMovieFromInitialFile` builds a pattern from the initial file's name: the name is regex-escaped, and each run of digits is replaced with `\d+`. A file is kept only if its whole name matches the pattern.
  - JES used `.*` unescaped. That pattern also matched names such as `frameX.png`, and treated the `.` before the extension as a wildcard. Our narrower pattern still accepts both 3-digit and 4-digit names.
- Sorting uses a natural-sort key: the name is split into digit and non-digit runs, and digit runs compare as integers. Ties are broken by the plain name. This fixes the plain `sorted()` misordering after frame 999.

### D6. Playback runs in a subprocess; stdin tells the player when to stop
```
 student script / Thonny backend                    player subprocess
 +-----------------------------------+              +------------------------------+
 | playMovie(movie)                  |              | python mediaCompMovie.py     |
 |  1. validate, resolve frames      |              |        --play manifest.json  |
 |  2. mkdtemp("mediaCompMovie-")    |              |  - thread: block on          |
 |     snapshots -> 0001.png ...     |   Popen      |    stdin.read(); EOF -> quit |
 |  3. write manifest.json           | -----------> |  - pygame window, clock      |
 |     {frames, fps, tempdir}        |  stdin=PIPE  |  - loop until close/Esc      |
 |  4a block:  proc.wait()           |              |  - on exit: rmtree(tempdir)  |
 |      finally: close stdin,        |              +------------------------------+
 |               terminate if alive  |
 |  4b non-block: keep proc in list, |
 |      return immediately           |
 +-----------------------------------+
```
- The command is `[sys.executable, os.path.abspath(__file__), "--play", manifest]`, the same mechanism `Picture.show()` uses.
- On Windows, the player is started with `creationflags=CREATE_NO_WINDOW` so no console window flashes up.
- `PYGAME_HIDE_SUPPORT_PROMPT=1` is set in the child's environment.
- **Liveness:** the parent keeps the write end of the child's stdin open. When the parent exits for any reason (the script ends, Ctrl+C, or Thonny Stop/Restart killing the backend), the OS closes that pipe. The child's reader thread sees EOF and posts a quit event. This works the same way on Windows and Linux, with no PID polling and no `psutil`.
  - `os.kill(pid, 0)` was rejected because on Windows it terminates the target process instead of checking it.
  - The reader thread uses `os.read(sys.stdin.fileno(), ...)`, not `sys.stdin.buffer.read()`. A daemon thread blocked in the buffered read holds the buffer's lock, and when the window is closed while the parent is still alive, Python 3.13 aborts at shutdown with `Fatal Python error: _enter_buffered_busy`.
- **Blocking mode:** `proc.wait()` sits inside `try/finally`. On `KeyboardInterrupt` the `finally` block closes stdin, which shuts the child down cleanly. It then calls `terminate()` if the child is still alive after a short timeout, and the interruption propagates to the script.
- **Non-blocking mode:** `Popen` objects are kept in a module-level list so they are not garbage-collected (that would close stdin and stop the player early). Finished entries are pruned on each call.
- **Temp files:** each playback writes every frame, whether a path or a snapshot, as a PNG into its own `tempfile.mkdtemp(prefix="mediaCompMovie-")` directory. The player removes that directory when it exits. In blocking mode the parent also removes it after `wait()`, in case the child was killed before it could.
  - Copying path frames too gives the "frames as at the time of the call" behaviour and a uniform manifest.
  - If the child is killed hard, the directory stays in the OS temp folder.
- **Player loop:**
  - The window size is the maximum width and height over all frames. Frames are drawn unscaled, centred on black.
  - Frames are loaded lazily and cached as pygame surfaces.
  - `pygame.time.Clock().tick(fps)` controls timing.
  - Title: `Movie: frame i of N`, with ` (paused)` added while paused.
  - Keys: space pauses and resumes; left and right step, wrapping around; Escape quits, as does the close button.
  - `_runPlayer` accepts a `maxFrames` test hook, so headless tests can run the loop without a display, using `SDL_VIDEODRIVER=dummy`. An `onTick(tick)` hook lets tests post key events into the running loop. The stdin watcher starts only when the file runs as the `--play` script (`watchStdin=True`), because pytest's `sys.stdin` cannot be read.

Alternatives considered:
- In-process pygame: blocks with no non-blocking option, clashes with mediaComp's hidden Tk root and wx `show` windows, and Thonny's Stop leaves the window frozen.
- Sending pickled frames over stdin, like `show.py`: it avoids temp files, but needs a custom protocol, and stdin is already used for liveness.

### D7. Export uses imageio's FFMPEG writer, one frame at a time
`_export(movie, path, fps, fmt)` runs these steps in order:
1. Validate the movie and fps.
2. Resolve the frames and check that there is at least one.
3. Import `imageio.v2` and `imageio_ffmpeg`. If that fails, print the hint and raise `ValueError`.
4. Check that the output folder exists.
5. Size pre-pass: open each frame lazily, which reads only its header, and compare its size with frame 1.
6. Open `imageio.v2.get_writer(path, format="FFMPEG", fps=fps, codec=..., pixelformat=..., macro_block_size=1, ...)`.
7. Stream frames: for each one, convert to RGB, pad to even dimensions with `np.pad(..., mode="edge")`, and append it.

| Format | Codec | Pixel format | Notes |
|---|---|---|---|
| mp4 | `libx264` | `yuv420p` | Plays in the Windows player; needs even dimensions |
| mov | `libx264` | `yuv420p` | Same encoder in a QuickTime container |
| avi | `mjpeg` | `yuvj420p` | Set quality via `quality=` or `-q:v`. H.264 in AVI often fails in the Windows player |

- All validation happens before the writer is opened, so a failed export never leaves a partial file.
- If an encoding error occurs after the writer has opened, the partial file is removed before the error is re-raised.
- Streaming avoids holding the whole movie as one numpy array: 300 frames at 640x480 would be about 276 MB with `np.stack`.
- Naming the FFMPEG format explicitly avoids imageio quietly switching to the PyAV plugin, which takes different arguments, if PyAV happens to be installed.

Alternative considered: `imageio.v3.imwrite` on a stacked array, as in the handoff. It is simpler, but its memory use is a problem, and the plugin it picks is unclear.

### D8. Module defaults with setters and getters
`DEFAULT_MOVIE_FORMAT = "mp4"` and `DEFAULT_PLAY_BLOCKING = True` are module globals. Students change them through `setMovieFormat`/`getMovieFormat` and `setPlayBlocking`/`getPlayBlocking`, because assigning the name after `from mediaCompMovie import *` only rebinds the student's own copy. This follows mediaComp's existing `setColorWrapAround`/`getColorWrapAround` pattern.

### D9. Test architecture
- **`tests/conftest.py`:**
  - Before anything imports mediaComp, sets `HOME` and `USERPROFILE` to a session temp directory, so `ConfigManager` reads and writes a throwaway `.mediaCompConfig` and never the developer's real one.
  - Inserts `contrib/movie` into `sys.path`.
  - Registers the `windows` marker with `config.addinivalue_line`, which avoids editing `pyproject.toml`.
  - In `pytest_collection_modifyitems`, adds the `windows` marker to everything under `tests/windows/`, and skips those tests unless `sys.platform == "win32"`.
  - Fixtures: `tmp_media` (a temp directory set as the media folder, reset afterwards), `cwd_tmp` (`chdir` into a temp directory), `frames_factory` (makes PNG/JPEG frames of a given size and mode), and `headless_sdl` (sets `SDL_VIDEODRIVER=dummy`).
- **Running the tests:**
  - In WSL, `pytest` runs `tests/movie` and skips `tests/windows`.
  - On Windows, `pytest -m windows` runs only the Windows tests, and `pytest` runs everything.
- **Export tests** use `pytest.importorskip("imageio_ffmpeg")`. The missing-dependency test simulates the missing packages by setting their entries in `sys.modules` to `None`, so it runs whether or not they are installed.
- **CI:** `pip install -e .` installs no imageio, so CI covers everything except real encoding. Encoding is covered in WSL and by `pytest -m windows` run manually on Windows with `requirements-dev.txt` installed.
- To get CI on this branch without editing the workflow, open a PR from `movies` into the fork's own `master` and never merge it.
- **Manual checks** go in `tests/windows/MANUAL_CHECKLIST.md`: Thonny with no extras, Thonny with export packages, playback speed and closing, Stop/Restart with no orphaned player, `show()` and `playMovie` together, a textbook animation script, and all three formats opened in the Windows player.

## Risks / Trade-offs

- **Thonny's `sys.executable` might not be the interpreter that has mediaComp.**
  - Mitigation: it is the backend interpreter, which is the one with mediaComp, since mediaComp imported successfully. Covered on the manual checklist.
- **The player window may open behind Thonny without focus.**
  - Mitigation: manual check. If it is a problem, request focus on Windows after the window is created (SDL hint or `SetForegroundWindow` through ctypes). The manual checklist (1.2) found the window opens in front of Thonny with keyboard focus, so no focus request is made.
- **MJPEG AVI might not play in a particular Windows player build.**
  - Mitigation: manual check on Windows 10 and 11. The fallback is `mpeg4` (MPEG-4 Part 2), which Windows has decoded natively since Windows 7. The manual checklist (6.2) found MJPEG AVI plays in the built-in player with no extra codecs, so the fallback is not used.
- **Stale frames:** `writeFramesToDirectory` overwrites `frame0001.png`… but leaves higher-numbered files from an earlier, longer run, and a later `makeMovie(dir)` would pick them up.
  - Mitigation: document this in the student README. A warning could be added later without changing the spec.
- **Snapshot memory:** very long or very large movies use a lot of RAM (D4).
  - Mitigation: acceptable for classroom use; noted in the README.
- **Temp directories leak if the player is hard-killed** (D6).
  - Mitigation: they live in the OS temp folder with a recognisable prefix.
- **An unexpected `mediaFolder` value:** if a student's config holds a media path without a trailing separator, `getMediaFolder(name)` still works because it uses `os.path.join`. That is unlike mediaComp's broken string concatenation.
- **The Phase 2 split may expose naming clashes with mediaComp,** for example `Movie` versus the stubs in `__init__.pyi`.
  - Mitigation: Phase 2 updates the stubs; the single file does not touch them.

## Migration Plan

Phase 1 (this change):
1. Implement and test on `movies`.
2. Complete the manual Windows checklist.
3. Give students `contrib/movie/mediaCompMovie.py` and its README.
4. Students roll back by deleting the file and the import line.

Phase 2 (a separate future change):
1. Open an issue upstream.
2. Branch from `master` and bring over only the code commits.
3. Split sections A/B/C into `models/Movie.py`, `core/movie.py` and `scripts/moviePlayer.py`; the player's `__file__` becomes the script path.
4. Update `core/__init__.py`, `__init__.py` (imports and `__all__`), `__init__.pyi` and `pyproject.toml` (an optional `movie` extra).
5. Report the `mediaFolder` bug separately.

## Open Questions

None. Both questions were resolved by the manual Windows checklist:

- Whether MJPEG AVI plays in the Windows built-in player: it does, without installing codecs (checklist 6.2). D7 keeps MJPEG; the `mpeg4` fallback was not needed.
- Whether the player window needs an explicit focus request on Windows: it does not. The window opens in front of Thonny and takes keyboard input without a click (checklist 1.2). D6 is unchanged.
