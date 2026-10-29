## Purpose

Lets students save their movies as video files (MP4, AVI or MOV) that play in Windows' built-in player, without breaking anything for students who have not installed the optional export packages.

## ADDED Requirements

### Requirement: Export functions
The module SHALL provide `writeMovie(movie, path, framesPerSec=16)`, `writeMP4(movie, path, framesPerSec=16)`, `writeAVI(movie, path, framesPerSec=16)` and `writeQuicktime(movie, path, framesPerSec=16)`. Each SHALL write the movie's frames, in order, to one video file at `framesPerSec` frames per second. Relative paths SHALL follow the relative path rules. An existing file at the target path SHALL be overwritten. The folder that will hold the file SHALL already exist.

#### Scenario: Export at the default rate
- **WHEN** `writeMP4(movie, "anim.mp4")` is called on a movie with 32 frames
- **THEN** `anim.mp4` exists, holds 32 frames, and plays at 16 frames per second

#### Scenario: Custom frame rate
- **WHEN** `writeAVI(movie, "anim.avi", 30)` is called
- **THEN** the file plays at 30 frames per second

#### Scenario: Missing output folder
- **WHEN** `writeMP4(movie, "nofolder/anim.mp4")` is called and `nofolder` does not exist
- **THEN** the error convention applies, and the message names the folder

### Requirement: Format-specific extensions
`writeMP4`, `writeAVI` and `writeQuicktime` SHALL write MP4, AVI and MOV files respectively. If the path does not already end in that format's extension (`.mp4`, `.avi`, `.mov`, any letter case), the extension SHALL be appended.

#### Scenario: Extension missing
- **WHEN** `writeAVI(movie, "anim")` is called
- **THEN** the file `anim.avi` is written

#### Scenario: Different extension given
- **WHEN** `writeQuicktime(movie, "anim.mp4")` is called
- **THEN** the file `anim.mp4.mov` is written

#### Scenario: Extension in upper case
- **WHEN** `writeMP4(movie, "anim.MP4")` is called
- **THEN** the file `anim.MP4` is written without another extension

### Requirement: Format chosen by extension, with a module default
`writeMovie` SHALL choose the format from the path's extension (`.mp4`, `.avi` or `.mov`, any letter case). A path with no extension SHALL get the format named by the module-level setting `DEFAULT_MOVIE_FORMAT`, which starts as `"mp4"`, and that extension SHALL be appended. Students SHALL be able to change and read the setting with `setMovieFormat(fmt)` and `getMovieFormat()`, which work after `from mediaCompMovie import *`. `setMovieFormat` SHALL accept `"mp4"`, `"avi"` or `"mov"` in any letter case, with or without a leading dot, and SHALL apply the error convention to anything else. Any other extension on a `writeMovie` path SHALL be an error.

#### Scenario: Format from the extension
- **WHEN** `writeMovie(movie, "anim.mov")` is called
- **THEN** a MOV file is written to `anim.mov`

#### Scenario: Default format
- **WHEN** `writeMovie(movie, "anim")` is called and `DEFAULT_MOVIE_FORMAT` has not been changed
- **THEN** an MP4 file is written to `anim.mp4`

#### Scenario: Changed default format
- **WHEN** a script that used `from mediaCompMovie import *` calls `setMovieFormat("avi")` and then `writeMovie(movie, "anim")`
- **THEN** an AVI file is written to `anim.avi`
- **AND** `getMovieFormat()` returns `"avi"`

#### Scenario: Invalid default format
- **WHEN** `setMovieFormat("gif")` is called
- **THEN** the error convention applies, the message lists the supported formats, and the setting is unchanged

#### Scenario: Unsupported extension
- **WHEN** `writeMovie(movie, "anim.gif")` is called
- **THEN** the error convention applies, and the message lists the supported formats

### Requirement: Export input validation
Every export function SHALL apply the error convention, without creating a file, when the first argument is not a movie, the movie has no frames, or `framesPerSec` is not a positive number.

#### Scenario: Not a movie
- **WHEN** `writeMP4("anim", "anim.mp4")` is called
- **THEN** the error convention applies and no file is created

#### Scenario: Empty movie
- **WHEN** `writeMP4(makeMovie(), "anim.mp4")` is called
- **THEN** the error convention applies and no file is created

#### Scenario: Invalid frame rate
- **WHEN** `writeMP4(movie, "anim.mp4", 0)` is called
- **THEN** the error convention applies and no file is created

### Requirement: Frame size consistency
All frames in an exported movie SHALL have the same width and height. If they do not, the export SHALL apply the error convention without creating a file. The message SHALL name the first frame that differs and give both sizes, numbering frames from 1.

#### Scenario: One frame of a different size
- **WHEN** frame 1 is 320x240, frame 12 is 640x480, and `writeMP4(movie, "anim.mp4")` is called
- **THEN** the error message says that frame 12 is 640x480 but frame 1 is 320x240
- **AND** no file is created

### Requirement: Frame normalisation
Export SHALL accept frames with or without transparency and in grayscale, and SHALL write them as full-colour frames; transparency is dropped. A frame with an odd width or height SHALL have one pixel row or column added to make it even, filled by repeating the edge pixels.

#### Scenario: Mixed colour modes
- **WHEN** a movie has some RGBA PNG frames and some RGB JPEG frames of the same size and is exported
- **THEN** the export succeeds

#### Scenario: Odd frame size
- **WHEN** a movie with 101x79 frames is exported
- **THEN** the export succeeds and the video's frames are 102x80

### Requirement: Playable in Windows' built-in player
Files written in each of the three formats SHALL play in the video player that comes with Windows 10 and 11 ("Media Player" / "Movies & TV") without installing extra codecs.

#### Scenario: Manual check on Windows
- **WHEN** an MP4, an AVI and a MOV file are exported from the same movie on Windows and opened in Windows' built-in player
- **THEN** each one plays and shows the movie's frames in order

### Requirement: Export without the optional packages
When the packages needed for export are not installed, every export function SHALL print the message `Movie export needs: pip install imageio imageio-ffmpeg (Thonny: Tools → Manage packages)` and raise `ValueError` without creating a file. Importing the module and every non-export function SHALL work without those packages.

#### Scenario: Export packages missing
- **WHEN** `writeMP4(movie, "anim.mp4")` is called and the export packages are not installed
- **THEN** the install message is printed, `ValueError` is raised, and no file is created

#### Scenario: Import without export packages
- **WHEN** a script runs `from mediaCompMovie import *` and the export packages are not installed
- **THEN** the import succeeds
