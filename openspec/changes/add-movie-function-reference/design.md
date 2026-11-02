## Context

See proposal.md for the motivation and specs/ for the required behaviour. This section covers only what shapes the implementation.

- **Upstream reference document.** `Documentation/Media Functions.pdf` is exported from `Documentation/Media Functions.docx` with Acrobat PDFMaker for Word. It is hand-written and is not generated from code; upstream functions have no docstrings.
  - **Styles:** `Title`, `heading 1`/`2`/`3`, a custom `Program code` style (Courier New, one paragraph per code line), and the `toc 1`–`3` styles.
  - **Table of contents:** a `TOC \o "1-3" \h \z \u` field.
  - **Page setup:** US Letter with 1-inch margins, and a header showing `Page N` through a PAGE field.
  - **Fonts:** the default font is Arial. The theme fonts are Calibri and Cambria.
  - **Footer:** David Largent's CC BY-NC-SA 4.0 notice on every page.
- **Tooling, checked on the development machine (Debian 13 "trixie" under WSL2; repo venv on Python 3.13.5):**
  - `python-docx` is not installed. LibreOffice, `python3-uno` and Carlito are not installed but are available from apt.
  - `ttf-mscorefonts-installer` (Arial and Courier New) is not available, because the apt `contrib` component is not enabled.
  - `pdftotext` is present.
- **Movie module.** `playMovie(movie, delay=None, framesPerSec=None, block=None)` builds a manifest with `fps` and starts the player subprocess. The player reads `fps` from the manifest, so it needs no change. `DEFAULT_PLAY_BLOCKING`, `setPlayBlocking` and `getPlayBlocking` exist only to serve `playMovie`.
- **mediaComp's `play`.** `play(sound, isBlocking=False)` passes `isBlocking` to `Sound.play`, which does `if isBlocking: sd.wait()`. Nothing is validated.
- **Evidence from JES and Guzdial behind the API choice:**
  - JES's student-facing functions never use keyword arguments; optional parameters are trailing positionals.
  - JES's `playMovie(movie)` has no speed parameter; `AnimationPanel.framesPerSec` is fixed at 16. JES chooses the frame rate only in `writeAVI`/`writeQuicktime(movie, path[, framesPerSec])`.
  - Guzdial's published code zip contains no `playMovie(movie, delay)` call outside the library itself.

## Goals / Non-Goals

**Goals:**
- One build command that turns the Markdown source into `Movie Functions.docx` and `Movie Functions.pdf` under WSL.
- The generated `.docx` is close enough to upstream that its sections can be pasted into upstream's file, or restyled by hand in minutes.
- The source is parsed by the same code in the build and in the drift test. The drift test needs neither `python-docx` nor LibreOffice, so it runs in the normal test suite and in CI.

**Non-Goals:**
- A general Markdown converter. The source uses a small, fixed subset.
- Matching upstream's PDF byte for byte, or exactly matching its fonts.
- Putting the generated files into the build or CI pipeline. They are built by hand and committed.
- Changing `Documentation/` or anything under `src/mediaComp/`.

## Decisions

### D1. File layout
```
contrib/movie/
  mediaCompMovie.py
  README.md                     setup, examples, short function list -> PDF
  Movie Functions.docx          generated, committed
  Movie Functions.pdf           generated, committed
  requirements-dev.txt          + python-docx
  docs/
    movie-functions.md          THE source (hand-edited)
    refdoc.py                   parser: source -> document model; shared with the test
    build.py                    model -> .docx (python-docx); then calls docx2pdf.py
    docx2pdf.py                 LibreOffice UNO helper: update TOC, export PDF
tests/movie/
  test_reference_doc.py         drift test (imports docs/refdoc.py)
```

### D2. Pipeline
```
 movie-functions.md
        |
        v
 refdoc.parse()  ------------------------------>  test_reference_doc.py
   document model:                                  vs mediaCompMovie.__all__
   front matter, sections,                          vs inspect.signature()
   entries {signatures, description,                ast.parse(every example)
            params, returns, examples}
        |
        v
 build.py (venv python + python-docx)
   open Documentation/Media Functions.docx as the style template (D4)
   clear body, write front matter, TOC field, sections, entries, appendix
   replace footer text
        |
        +--> contrib/movie/Movie Functions.docx
        |
        v
 docx2pdf.py (/usr/bin/python3 + python3-uno, started by build.py)
   soffice --headless; load .docx; update all indexes (TOC page numbers); export PDF
        |
        +--> contrib/movie/Movie Functions.pdf
```
`build.py` writes nothing until parsing and validation succeed (the "Malformed entry" scenario). If LibreOffice or `python3-uno` is missing, it still writes the `.docx`. It then prints which apt packages to install and exits non-zero, so a stale PDF is never mistaken for a fresh one.

### D3. Source format (`movie-functions.md`)
The source is a strict subset of Markdown, so it reads well on GitHub and can be parsed with a short hand-written parser (no Markdown library):
```
---
title: mediaCompMovie
subtitle: Movie functions for mediaComp
basedOn: <what this documents, e.g. "mediaCompMovie, movies branch">
date: 2026-10-30
footer: <author and license line>
---

# About this document           <- Heading 1; free paragraphs and "- " bullets
...
# Movie Functions               <- the function section
<preamble paragraphs and bullets>

## addFrameToMovie(frame, movie)   <- consecutive "##" lines = one shared entry
Description; *frame* is italic; `code` is Courier.

frame: the picture, or the name of an image file, to add
movie: the movie to add it to
returns: nothing

```python                        <- one example; repeatable
addFrameToMovie(canvas, movie)
```
One sentence explaining the example.

# Appendix A: Differences from the JES movie functions
### playMovie(movie[, isBlocking])   <- Heading 3 sub-entries, free text
```
- **Inline markup:** only `*italic*` and `` `code` ``.
- **Entries:** a function entry is a `##` heading inside the function section. A block of `name: text` lines that ends with `returns:` is the parameter block. "Optional" is written into the parameter text as `(optional)`, as upstream does.
- **Rejected alternative:** YAML or JSON per function. It would be easier to parse but harder to write prose in. Markdown keeps the source readable, and it is what an upstream reviewer would most likely accept.

### D4. Upstream's `.docx` as the style template
`build.py` opens `Documentation/Media Functions.docx` with python-docx, deletes every body element except the final section properties, and replaces the footer paragraph's text with the source's `footer` field. Everything else is inherited unchanged:
- the style definitions, including `Program code`
- the theme fonts
- the page size and margins
- the `Page N` header

That makes "uses upstream's styles" true by construction. A section copied into upstream's file keeps its look, because the style names are identical and Word's paste uses the destination's styles.

Alternatives considered:
- *Define the styles from scratch in python-docx.* That means more code, and it drifts from upstream whenever their document changes.
- *pandoc with `--reference-doc`.* It gives the same styles, but code blocks need a Lua filter to map to `Program code`. It can't do the strict entry checking, and it adds a non-Python tool.

Risk: if upstream restructures their `.docx` (for example renames `Program code`), the build fails loudly on the missing style rather than producing wrong output.

### D5. Rendering rules
- **Function headings.** One `Heading 2` paragraph per signature; grouped signatures get consecutive `Heading 2` paragraphs. Section headings use `Heading 1`, appendix sub-entries `Heading 3`, and the title `Title` (with the subtitle, `basedOn` and `date` lines below it as in upstream).
- **Descriptions and parameter lines.** Descriptions are `Normal` paragraphs, with each `*x*` as an italic run. Parameter lines are `Normal` paragraphs, written exactly as `name: text`, which is what upstream does.
- **Examples.** One `Program code` paragraph per source line, keeping leading spaces (python-docx keeps them when set as run text). The label "Example:", or "Examples:" when there is more than one, is a `Normal` paragraph before the first one, as upstream does.
- **Table of contents.** A `TOC \o "1-3" \h \z \u` complex field with placeholder text. `w:updateFields` is set in `settings.xml` so Word refreshes it on open, and `docx2pdf.py` refreshes it for the PDF.
- **Bullets.** `List Paragraph` with upstream's bullet numbering if python-docx can reach it. Otherwise a plain `•` prefix. Bullets are only used in the front matter.

### D6. Drift test (`tests/movie/test_reference_doc.py`)
- **Signature parsing.** The test imports `refdoc` by path (`contrib/movie/docs` is not a package) and parses each heading into `(name, [(param, optional)])`. It handles nested brackets, so `f(a[, b[, c]])` and `f(a[, b][, c])` both mark `b` and `c` optional.
- **Signature comparison.** The parsed form is compared with `inspect.signature(getattr(mediaCompMovie, name))`:
  - the parameter names must appear in the same order
  - `optional` must equal `param.default is not inspect.Parameter.empty`
  - there must be no `*args`, `**kwargs` or keyword-only parameters
- **Coverage and examples.**
  - The set of documented names must equal `set(__all__)`, and each name must be documented exactly once.
  - Each entry's parameter-line names must equal the union of its signatures' parameters, followed by exactly one `returns:` line.
  - Every example must pass `ast.parse`.
- **Failure messages.** Each failure names the function or entry. The test is parametrized per public name, so pytest's output shows which one failed.

### D7. `playMovie` simplification
- **Signature.** `def playMovie(movie, isBlocking=False)`, with error-convention signature string `"playMovie(movie[, isBlocking])"`. The manifest always gets `"fps": 16`, written as a module constant `PLAYBACK_FPS = 16` that is not part of `__all__`. That is the hook for the future speed keys.
- **Blocking test.** `if isBlocking:` chooses the blocking path, the same test `Sound.play` uses. A non-boolean is never an error.
- **Removals.**
  - `DEFAULT_PLAY_BLOCKING`, `setPlayBlocking` and `getPlayBlocking` are deleted, and the two names leave `__all__`.
  - The `delay`/`framesPerSec` validation and the "give either, not both" error are deleted.
  - `_isPositiveNumber` stays, because export uses it.
- **Unchanged.** The non-blocking `_players` bookkeeping and the blocking `try/finally` stay as they are. Only the default flips.
- **Rejected alternative:** validating `isBlocking` as True/False/1/0, so that `playMovie(movie, 0.1)` fails loudly. The instructor chose to match `play()` exactly; the consequence is listed under Risks.

### D8. Tooling installation (documented in `docs/build.py --help` and the README's developer note)
```
sudo apt install libreoffice-writer-nogui python3-uno \
                 fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea
venv/bin/pip install -r contrib/movie/requirements-dev.txt     # adds python-docx
```
- **Fonts.** `fonts-liberation` provides Liberation Sans and Mono, which have the same metrics as Arial and Courier New; LibreOffice substitutes them automatically, so the layout matches without the Microsoft fonts. For exact fonts, enable apt `contrib` and install `ttf-mscorefonts-installer`. Alternatively, open the `.docx` in Word on Windows and save it as PDF.
- **Python split.** `docx2pdf.py` runs under `/usr/bin/python3`, because `python3-uno` is a system package that the venv can't see. `build.py` finds the interpreter with `shutil.which("python3")` limited to `/usr/bin`, and reports clearly if it can't `import uno`.

## Risks / Trade-offs

- **Old scripts change behaviour without an error.**
  - Old Guzdial-style calls like `playMovie(movie, 0.1)` now block at 16 fps instead of showing each frame for 0.1 s.
  - Scripts that relied on the old blocking default no longer wait.
  - Mitigation: the movie module has not yet been given to students. The appendix and README state the change. `block=` and the setters fail loudly (`TypeError`/`NameError`).
- **Non-blocking by default in a loop.** `for m in movies: playMovie(m)` opens every window at once. Mitigation: the `playMovie` entry and its example say to pass `True` to watch one movie at a time.
- **Non-blocking outside Thonny.** When the script ends, the parent process exits, and the window closes immediately. Mitigation: the reference says to pass `True` when running scripts outside Thonny. The clean-shutdown behaviour itself is unchanged.
- **LibreOffice TOC and layout differ slightly from Word's.** Page breaks and TOC page numbers in the PDF may not match what Word would produce from the same `.docx`. Mitigation: accepted. The `.docx` is the hand-off format, and Word refreshes the TOC on open.
- **UNO automation is fragile.** A leftover `soffice` process or a locked profile can hang the conversion. Mitigation: `docx2pdf.py` starts its own `soffice` with a throw-away `-env:UserInstallation` profile in a new unique temp directory, uses a timeout, and terminates the process on exit. Per the house rules, it leaves the temp directory in place and reports its path.
- **The template couples the build to upstream's file.** Mitigation: the build checks that the required styles exist and names any missing one.
- **Three descriptions of each function** (docstring, README list, reference). The drift test covers only the reference's signatures. Mitigation: the README keeps only names and points to the PDF, and docstrings remain the developer view. A docstring check can be added later if they drift.
- **Differences from upstream's PDF, found by comparing rendered pages (task 4.3).** The build copies upstream's horizontal rule between entries and the rules under the title lines, so the layout, headings, bold parameter labels, header page number and margins match. What still differs, and would need hand restyling for upstream:
  - **Fonts in the PDF.** LibreOffice substitutes Caladea for Cambria (body), Carlito for Calibri (headings) and Liberation Mono for Courier New (code). The metrics are the same, so line breaks match, but Liberation Mono looks lighter than Courier New. The `.docx` still names upstream's fonts, so Word uses the originals.
  - **Code in running text.** The reference sets file names, literal values and short calls such as `makeMovie(directory)` in Courier (upstream's `Program code Char` style). Upstream never uses Courier in prose; it writes such text plainly or bolds function names. This is deliberate for students, but upstream may want those runs restyled.
  - **Example labels.** An entry with two examples gets one "Examples:" label (D5). Upstream is inconsistent: `getMediaFolder` has one "Example:" for two examples, `play` repeats "Example:" before each.
  - **Title block and footer.** There is no institution line between the subtitle and "Document based on", and the footer is one plain-text line with no hyperlink. Upstream's footer is two lines with a link to the license.
  - **Table of contents.** LibreOffice builds it, so page numbers can differ from Word's; Word refreshes it on open. The larger type of the Heading 3 lines comes from upstream's own `toc 3` style, which Word renders the same way.

## Migration Plan

1. Land the `playMovie` change, its tests and the README updates in one commit, so the module and its documentation never disagree.
2. Add the source, parser, drift test and build. Generate and commit `Movie Functions.docx` and `.pdf`.
3. Re-run the affected rows of the manual Windows checklist (2.x and 3.x) with the new signature before giving the module to students.

Rollback is a revert of those commits. No persistent state or student data is involved.

## Open Questions

- **The footer's author and license line.** The instructor decides this before the handout goes to students. It is one field in the source's front matter; until then it holds a clearly marked placeholder that the build prints a warning about.

## Future Work (recorded, not in this change)

- **Player speed keys.** Up and down arrows would double or halve the playback rate (starting from `PLAYBACK_FPS`), and the window title would show the current rate, e.g. `Movie: frame 3 of 29 (32 fps)`. This gives students speed control in the preview without adding a parameter.
- **Upstream issue, together with the `mediaFolder` bug.** These are errors found in `Documentation/Media Functions.pdf` (v0.4.7 text):
  - `requestIntegerInRange(message)` leaves out its min/max parameters, although its example passes them.
  - The `requestNumber` example calls `requestInteger`.
  - The `getDuration`, `getNumSamples` and `getSamples` examples use Python 2 `print x`.
  - `def` lines without a colon in the `getHeight`, `getWidth`, `getPixelAt` and `getSampleAt` examples.
  - A `makeEmptySoundBySecons` typo, and "22,050 bits/second" where it should say samples per second.
  - `getSampleValueAt` is described as returning a Sample object, but it returns a value.
  - The `duplicatePicture` parameter line says `pic`, not `picture`.
  - The `getMediaFolder` example uses `"C:\"`, which is not a valid Python string.
  - `getPixels` has a doubled "returns:".
  - `setMediaPath` is listed twice in Appendix B.
  - The document is stamped v0.4.7, but the package is at 0.4.15.
- **Upstream integration.** Decide with the maintainer whether the movie section is inserted into `Media Functions.docx` (D4 makes that a copy and paste), shipped as a separate document, or whether upstream adopts the Markdown build for the whole reference.
