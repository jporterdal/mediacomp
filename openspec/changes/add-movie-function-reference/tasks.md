## 1. Simplify playMovie (spec: movie-playback)

- [ ] 1.1 In `contrib/movie/mediaCompMovie.py`, change `playMovie` to `playMovie(movie, isBlocking=False)` (design D7). The changes:
  - add `PLAYBACK_FPS = 16` and always write it to the manifest
  - block only `if isBlocking:`
  - set the error signature string to `"playMovie(movie[, isBlocking])"`
  - delete the `delay`/`framesPerSec`/`block` handling
  - update the docstring

  Verify that `venv/bin/python -c "import inspect,sys; sys.path.insert(0,'contrib/movie'); import mediaCompMovie as m; print(inspect.signature(m.playMovie))"` prints `(movie, isBlocking=False)`.
- [ ] 1.2 Delete `DEFAULT_PLAY_BLOCKING`, `setPlayBlocking` and `getPlayBlocking`, and remove the two names from `__all__`. Update `EXPECTED` in `tests/movie/test_public_names.py` to the 12 remaining names. Verify that `venv/bin/pytest tests/movie/test_public_names.py` passes.
- [ ] 1.3 Rewrite `tests/movie/test_playback.py` for the new behaviour:
  - Drop the `DEFAULT_PLAY_BLOCKING` reset in the `player_state` fixture.
  - Remove the tests for `delay`/`framesPerSec`, for "both given" and for the setters.
  - Change `block=False` calls to `playMovie(movie)` and `block=True` calls to `playMovie(movie, True)`.
  - Add tests that:
    - the default call does not block
    - `playMovie(movie, 1)` and `playMovie(movie, 0.1)` block, and `playMovie(movie, 0)` does not
    - the manifest's `fps` is 16
    - `framesPerSec=`, `delay=` and `block=` raise `TypeError` before any `Popen`
    - `setPlayBlocking`/`getPlayBlocking` are absent after `from mediaCompMovie import *`

  Verify that `venv/bin/pytest tests/movie` passes.
- [ ] 1.4 Update `tests/windows/test_player_win.py`: replace `block=False` with the default call. Verify with `venv/bin/pytest tests/windows --collect-only` that it still collects, since it only runs on Windows.
- [ ] 1.5 Update `tests/windows/MANUAL_CHECKLIST.md`:
  - Row 2.2 (delay) and row 2.3 (`framesPerSec=4`) become a single check that playback runs at 16 fps.
  - Rows 3.2 and 3.7 drop `block=False`.
  - Any row whose script expects `done` only after the window closes uses `playMovie(movie, True)`.
  - Add a row for `writeMP4(movie, "anim.mp4", 4)` playing at 4 fps in the Windows player.

  Verify by reading the checklist that no `delay`, `framesPerSec=` (other than on `write*`), `block=` or `setPlayBlocking` text remains (`grep -nE 'block=|setPlayBlocking|framesPerSec=|, 0\.(1|25)\)' tests/windows/MANUAL_CHECKLIST.md` prints nothing).

## 2. Tooling

- [ ] 2.1 Add `python-docx` to `contrib/movie/requirements-dev.txt` and install it into `venv`. Verify that `venv/bin/python -c "import docx"` succeeds.
- [ ] 2.2 Install the PDF tooling in WSL (design D8): `libreoffice-writer-nogui python3-uno fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea`. Ask the instructor before running `sudo apt install`. Verify that `soffice --version` runs, `/usr/bin/python3 -c "import uno"` succeeds, and `fc-list | grep -iE 'liberation|carlito'` lists the fonts.

## 3. Reference source and parser (spec: movie-reference-doc)

- [ ] 3.1 Write `contrib/movie/docs/refdoc.py` (design D3, D6). It contains:
  - the front-matter reader
  - the section, paragraph, bullet and fenced-block reader, with `*italic*` / `` `code` `` inline runs
  - the entry builder for consecutive `##` signature headings, description, parameter block and examples
  - the signature parser, which handles nested and sequential brackets
  - validation that raises one error naming the entry and the missing part

  Verify with a short throw-away source in the scratchpad: a well-formed entry parses into the expected model, and an entry without `returns:` or without an example raises an error naming that entry.
- [ ] 3.2 Write `tests/movie/test_reference_doc.py`. It loads `refdoc` by path, parses `contrib/movie/docs/movie-functions.md`, and checks:
  - coverage against `__all__`, with no duplicates and no non-public entries
  - each signature against `inspect.signature`, both names and order, and that brackets mark exactly the parameters with defaults
  - that the parameter lines match the signature parameters
  - `ast.parse` on every example

  Parametrize the checks per public name. Verify that the test fails with clear, named messages against a deliberately incomplete stub source, written in the scratchpad and passed through a fixture or monkeypatch, before the real source exists.
- [ ] 3.3 Write `contrib/movie/docs/movie-functions.md`:
  - **Front matter:** title, subtitle, `basedOn`, `date`, and `footer` set to a marked placeholder (open question).
  - **"About this document":** what the document covers, plus upstream's syntax conventions (`[ ]` optional, italic parameters, Courier examples).
  - **"Movie Functions" preamble:**
    - the two import lines
    - fixed 16 fps playback, with the rate chosen when saving
    - `frame0001.png` naming
    - relative paths and the media folder
    - the optional `imageio`/`imageio-ffmpeg` packages and the install hint
    - same-size frames for export
    - old leftover frame files and memory use, moved from the README
  - **Entries:** one per public function, in alphabetical order. `setMovieFormat` and `getMovieFormat` get separate entries, as upstream does for wrap-around. Each has a Python 3 example built from mediaComp functions and an explanation sentence. The `playMovie` entry explains when to pass `True`.

  Verify that `venv/bin/pytest tests/movie/test_reference_doc.py` passes.
- [ ] 3.4 Write the appendix "Differences from the JES movie functions":
  - `playMovie`: no frame rate, loops, does not wait by default, `isBlocking`; Guzdial's `delay` is not supported
  - PNG frames with 4-digit names instead of JPEG
  - the default folder for `writeFramesToDirectory` is the current folder, not home
  - `addFrameToMovie` also accepts pictures
  - `writeAVI`/`writeQuicktime` no longer need the frames in one folder, but need the export packages
  - additions not in JES: `makeMovie(directory)` and `writeFrame` from Guzdial's notebooks; `writeMP4`, `writeMovie`, `setMovieFormat`, `getMovieFormat`
  - not provided: `explore(movie)` and `openFrameSequencerTool`

  Verify that the drift test still passes, and that `refdoc` parses the appendix's `###` sub-entries.

## 4. Build the handout

- [ ] 4.1 Write `contrib/movie/docs/build.py` (design D2, D4, D5):
  - open `Documentation/Media Functions.docx` as the template, check the required styles exist, and clear the body
  - write the title block, TOC field (with `updateFields`), sections, entries (`Heading 2` signatures, italic parameters, `Program code` example lines with leading spaces kept) and the appendix (`Heading 3`)
  - replace the footer text, and warn while it is still the placeholder
  - write nothing if parsing fails

  Verify that running it with `--no-pdf` writes `contrib/movie/Movie Functions.docx`. Check with python-docx that every signature paragraph has style `Heading 2`, every example line `Program code`, and that the footer contains no "Largent".
- [ ] 4.2 Write `contrib/movie/docs/docx2pdf.py` (design D8). It:
  - runs under `/usr/bin/python3`
  - starts `soffice --headless` with a throw-away profile in a new unique temp directory and a timeout
  - loads the `.docx`, updates all document indexes and exports a PDF
  - terminates `soffice` and reports the temp directory it leaves

  Connect it to `build.py` with clear messages when LibreOffice or `uno` is missing. Verify that `venv/bin/python contrib/movie/docs/build.py` writes `contrib/movie/Movie Functions.pdf`, and that `pdftotext` on it shows the TOC with page numbers and every function heading.
- [ ] 4.3 Visually check the PDF against `Documentation/Media Functions.pdf`: rasterise two or three pages with `pdftoppm` into the scratchpad and compare the headings, code font, header page number, margins and footer. Record any differences that need hand restyling for upstream in the change's design.md under Risks. Verify by sending the instructor the rendered pages for a look.
- [ ] 4.4 Test the copy into upstream: paste the generated Movie Functions section into a scratch copy of `Media Functions.docx` and convert it with LibreOffice. Do this in the scratchpad, never in `Documentation/`. Verify with `pdftotext` that the pasted section uses the same heading and code formatting as the surrounding upstream sections (spec scenario "Copying into the upstream document").

## 5. README and wrap-up

- [ ] 5.1 Update `contrib/movie/README.md`:
  - the folder example uses `playMovie(movie)` with no delay
  - the blocking text describes `playMovie(movie, True)` and the non-blocking default
  - the function table becomes a short list of the 12 signatures that tells students to read `Movie Functions.pdf`
  - the "Things to watch out for" content moves into the reference (a one-line pointer is kept)
  - a short developer note says how to rebuild the handout

  Verify that `grep -nE 'block=|setPlayBlocking|getPlayBlocking|framesPerSec=|playMovie\(movie, 0' contrib/movie/README.md` prints nothing.
- [ ] 5.2 Run the full portable suite, `venv/bin/pytest`, and confirm that everything passes. Then rebuild both handouts from a clean state and confirm that `git status` shows only the intended files changed: no edits under `Documentation/` or `src/`.
- [ ] 5.3 Ask the instructor for the footer's author and license line. Put it in the front matter, rebuild, and verify that the build no longer warns about the placeholder and that `pdftotext` shows the new footer on every page.
- [ ] 5.4 Re-run the changed rows of `tests/windows/MANUAL_CHECKLIST.md` on Windows with Thonny, at least 2.x and 3.x with the new signature. Record the results the same way as for add-movie-support. Verify that each changed row is marked pass or has a noted issue.
