## Purpose

Gives students a printable reference for the movie functions, in the same form as mediaComp's own "Media Functions" document: what each function does, its parameters and return value, and an example. It is built from one source that is checked against the code, so it can later be offered upstream.

## ADDED Requirements

### Requirement: Single source of truth
The reference SHALL have exactly one hand-edited source: a Markdown file kept in the repository. The `.docx` and `.pdf` handouts SHALL be generated from that source by a build command, and SHALL NOT be edited by hand in the repository. The build SHALL run on the development machine (WSL/Linux) without Microsoft Word.

#### Scenario: Regenerate after an edit
- **WHEN** a function's description is changed in the Markdown source and the build command is run
- **THEN** the regenerated `.docx` and `.pdf` both contain the new description

#### Scenario: Build without Word
- **WHEN** the build command is run in WSL with the documented development tools installed
- **THEN** it produces both `Movie Functions.docx` and `Movie Functions.pdf`

#### Scenario: Malformed entry
- **WHEN** the Markdown source contains a function entry that is missing its `returns:` line or its example
- **THEN** the build stops with a message that names the entry and what is missing, and writes no output files

### Requirement: Entry format matches the upstream reference
Each function entry SHALL follow the format of mediaComp's "Media Functions" document, in this order:
- **Heading:** the signature. Optional parameters SHALL be shown in square brackets, for example `writeAVI(movie, path[, framesPerSec])`. No signature SHALL use keyword-argument syntax (`name=value`).
- **Description:** one or more sentences that state any default values. Parameter names SHALL appear in italics.
- **Parameter lines:** one line per parameter, `name: description`. An optional parameter's line SHALL end with `(optional)`.
- **Return line:** `returns:` with a description, or `returns: nothing`.
- **Example:** at least one, each followed by a sentence explaining what it does.

Functions whose descriptions would be nearly identical MAY share one entry with several signature headings, as upstream does for `addRect` and `addRectFilled`. Entries within a section SHALL be in alphabetical order.

#### Scenario: Optional parameter shown in brackets
- **WHEN** the reference shows `writeFramesToDirectory`
- **THEN** its heading is `writeFramesToDirectory(movie[, directory])` and the *directory* line ends with `(optional)`

#### Scenario: Function with no result
- **WHEN** the reference shows `addFrameToMovie`
- **THEN** its entry includes the line `returns: nothing`

#### Scenario: Alphabetical order
- **WHEN** the Movie Functions section is read from top to bottom
- **THEN** the entries appear in alphabetical order of function name

### Requirement: Reference stays in step with the code
An automated check in the test suite SHALL compare the Markdown source with the movie module. It SHALL fail, naming the function, when:
- a public name of the module (its `__all__`) has no entry, or has more than one
- an entry documents a function that is not public
- a signature heading's parameter names or their order differ from the function's
- a signature heading's brackets do not mark exactly the parameters that have default values
- an entry's parameter lines do not list exactly the parameters in its heading

Every example SHALL be valid Python 3 syntax, and the check SHALL fail on an example that is not.

#### Scenario: Function added without documentation
- **WHEN** a new public function is added to the module but not to the Markdown source
- **THEN** the check fails and names the function

#### Scenario: Signature changed in code only
- **WHEN** a parameter of a public function is renamed in the code but not in the reference
- **THEN** the check fails and names the function

#### Scenario: Python 2 example
- **WHEN** an example contains `print "done"`
- **THEN** the check fails and names the entry

### Requirement: Generated document uses upstream's styles
The generated `.docx` SHALL use the paragraph and character style names of mediaComp's `Media Functions.docx`:
- `Title` for the title
- `Heading 1` for each section
- `Heading 2` for each function signature
- `Heading 3` for appendix sub-entries
- a style named `Program code` for every example line
- italics for parameter names in descriptions

It SHALL use US Letter pages with 1-inch margins, a page number in the header, and a table of contents. That way a section can be copied into the upstream document, or restyled by hand, without rebuilding its structure. Exact font matching with the upstream PDF is not required.

#### Scenario: Example lines styled as code
- **WHEN** the generated `.docx` is opened in Word or LibreOffice
- **THEN** every example line uses the `Program code` style, and every function signature uses `Heading 2`

#### Scenario: Copying into the upstream document
- **WHEN** the Movie Functions section is copied from the generated `.docx` into upstream's `Media Functions.docx`
- **THEN** its headings and example lines take on upstream's formatting without manual restyling

### Requirement: Content of the reference
The reference SHALL contain:
- a title, a short statement of what the document covers, a document date, and the `mediaCompMovie` version or commit it describes
- the upstream syntax conventions: square brackets mark optional parameters, italics mark parameter names, and examples are in a fixed-width font
- a "Movie Functions" section that opens with a short preamble. The preamble SHALL cover:
  - the two import lines
  - that playback always runs at 16 frames per second and the rate is chosen when saving
  - frame files named `frame0001.png`, `frame0002.png`, …
  - how relative paths are resolved against the media folder
  - that saving videos needs the optional `imageio` and `imageio-ffmpeg` packages, with the install hint
  - that all frames must be the same size to save a video
- one entry for every public movie function
- an appendix listing how the movie functions differ from the JES movie functions, for students and instructors working from the textbook

Every page SHALL carry a footer naming the reference's author and license. The footer SHALL NOT reproduce the upstream document's copyright notice.

#### Scenario: Student looks up how to save a video at a given speed
- **WHEN** a student reads the `writeMP4` entry
- **THEN** it states that *framesPerSec* is optional, that the default is 16, and that the optional export packages must be installed

#### Scenario: Instructor checks a textbook program
- **WHEN** an instructor reads the appendix
- **THEN** it says that `playMovie` takes no frame rate and does not wait by default, that frames are written as PNG rather than JPEG, and which functions are additions not found in JES

### Requirement: Handout location
The generated `Movie Functions.docx` and `Movie Functions.pdf` SHALL be committed next to `mediaCompMovie.py`, so that students who download the module find the reference beside it. The module's README SHALL point students to the PDF for the full function reference.

#### Scenario: Student downloads the movie folder
- **WHEN** a student copies the contents of the movie folder
- **THEN** `Movie Functions.pdf` is beside `mediaCompMovie.py`, and the README tells them to read it
