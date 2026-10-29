# movie-frames Specification

## Purpose

Defines the movie object students build animations with: how movies are created in the textbook JES style and in Guzdial's notebook style, how frames are added, loaded and written as numbered images, and how file paths are resolved.

## Requirements

### Requirement: Error reporting convention
Every movie function SHALL report invalid input the way mediaComp does: print a message of the form `functionName(arguments): description`, then raise `ValueError`.

#### Scenario: Invalid input to a movie function
- **WHEN** a movie function is called with an argument of the wrong type
- **THEN** a line naming the function and its arguments, followed by a description of the problem, is printed
- **AND** `ValueError` is raised

### Requirement: Relative path resolution
Every movie function that takes a file or directory path SHALL resolve a relative path against mediaComp's media folder (`getMediaFolder()`). When no media folder is set, it SHALL resolve against the current working directory. This SHALL work even though mediaComp's own `makePicture` and `writePictureTo` fail on relative paths.

#### Scenario: No media folder set
- **WHEN** no media folder is set and a movie function is given the relative path `frames/frame0001.png`
- **THEN** the path refers to `frames/frame0001.png` under the current working directory

#### Scenario: Media folder set
- **WHEN** the media folder is set to `C:\media\` and a movie function is given the relative path `frames`
- **THEN** the path refers to `C:\media\frames`

#### Scenario: Absolute paths are used as given
- **WHEN** a movie function is given an absolute path
- **THEN** the path is used without change

### Requirement: Create an empty movie
`makeMovie()` called with no argument SHALL return a new movie with no frames and no directory.

#### Scenario: Empty movie
- **WHEN** `makeMovie()` is called
- **THEN** a movie is returned whose frame count is 0
- **AND** printing it shows `Movie, frames: 0`

### Requirement: Create a movie tied to a frame directory
`makeMovie(directory)` SHALL return a new movie with no explicitly added frames whose directory is `directory`, resolved under the relative path rules. The directory does not need to exist or contain frames when the movie is created.

#### Scenario: Movie with a directory
- **WHEN** `makeMovie("frames")` is called
- **THEN** a movie is returned whose directory is the resolved `frames` path

#### Scenario: Directory is not a string
- **WHEN** `makeMovie(42)` is called
- **THEN** the error convention applies

### Requirement: Frames come from the directory when none were added
If a movie has no explicitly added frames but has a directory, then whenever the movie is played, exported or written to a directory, its frames SHALL be the image files (`.png`, `.jpg`, `.jpeg`, any letter case) in that directory at that moment, ordered as described in "Numeric frame ordering". Explicitly added frames SHALL always take precedence over the directory.

#### Scenario: Guzdial workflow
- **WHEN** a script calls `writeFrame` for frames 1 to 30 into `frames`, then `playMovie(makeMovie("frames"))`
- **THEN** the movie plays those 30 frames in numeric order

#### Scenario: Directory contents change after the movie is created
- **WHEN** a movie is created with `makeMovie("frames")` and frame files are written to `frames` afterwards
- **THEN** playing or exporting the movie uses the files present at the time of playing or exporting

#### Scenario: Non-image files are ignored
- **WHEN** the movie's directory contains `frame001.png`, `frame002.png` and `notes.txt`
- **THEN** the movie's frames are the two PNG files

### Requirement: Numeric frame ordering
Wherever frames are taken from a set of files, they SHALL be ordered by the numbers in their file names, compared as numbers. Ties SHALL be broken by plain file name order.

#### Scenario: Frame numbers wider than the zero padding
- **WHEN** the frame files are `frame998.png`, `frame999.png` and `frame1000.png`
- **THEN** the order is `frame998.png`, `frame999.png`, `frame1000.png`

#### Scenario: Mixed padding widths
- **WHEN** the frame files are `frame002.png` and `frame0001.png`
- **THEN** the order is `frame0001.png`, `frame002.png`

### Requirement: Load a movie from an initial frame file
`makeMovieFromInitialFile(filename)` SHALL return a movie whose frames are every file in the same directory as `filename` whose name matches `filename` once each run of digits is allowed to be any run of digits. The frames SHALL be ordered by numeric frame order. The file `filename` itself SHALL exist.

#### Scenario: Load a numbered sequence
- **WHEN** the directory contains `frame0001.png` to `frame0050.png` and `makeMovieFromInitialFile("frame0001.png")` is called
- **THEN** the movie has 50 frames in numeric order

#### Scenario: Both naming widths load
- **WHEN** the directory contains `frame001.png` to `frame012.png` (3-digit, Guzdial style) and `makeMovieFromInitialFile("frame001.png")` is called
- **THEN** the movie has 12 frames

#### Scenario: Unrelated files are excluded
- **WHEN** the directory contains `frame0001.png`, `frame0002.png`, `frame0001.jpg` and `background.png`
- **THEN** `makeMovieFromInitialFile("frame0001.png")` loads only `frame0001.png` and `frame0002.png`

#### Scenario: Initial file does not exist
- **WHEN** `makeMovieFromInitialFile("missing0001.png")` is called and that file does not exist
- **THEN** the error convention applies, and the message names the path that was looked for

### Requirement: Add a frame to a movie
`addFrameToMovie(frame, movie)` SHALL append one frame to the end of the movie. The two arguments SHALL be accepted in either order. `frame` SHALL be either a path to an existing image file or a mediaComp `Picture`.

#### Scenario: Add a file path
- **WHEN** `addFrameToMovie("frame0001.png", movie)` is called and the file exists
- **THEN** the movie's frame count increases by 1 and its last frame is that file

#### Scenario: Arguments in reverse order
- **WHEN** `addFrameToMovie(movie, picture)` is called
- **THEN** the result is the same as `addFrameToMovie(picture, movie)`

#### Scenario: Add a Picture
- **WHEN** `addFrameToMovie(picture, movie)` is called with a mediaComp `Picture`
- **THEN** the movie's frame count increases by 1

#### Scenario: Missing frame file
- **WHEN** `addFrameToMovie("nope.png", movie)` is called and the file does not exist
- **THEN** the error convention applies, and the message names the path

#### Scenario: Neither argument is a movie
- **WHEN** `addFrameToMovie("a.png", "b.png")` is called
- **THEN** the error convention applies

#### Scenario: Frame is neither a path nor a Picture
- **WHEN** `addFrameToMovie(42, movie)` is called
- **THEN** the error convention applies

### Requirement: Picture frames are snapshots
A `Picture` added to a movie SHALL be stored as it looks at the moment it is added. Changing the same `Picture` object afterwards SHALL NOT change frames that were already added.

#### Scenario: Reusing one Picture while building frames
- **WHEN** a script draws on one `Picture`, adds it to a movie, draws something else on the same `Picture`, and adds it again
- **THEN** the movie has two frames that show the two different drawings

### Requirement: Describe a movie
A movie SHALL report its frame count through `len(movie)`, allow frame access by index (`movie[i]`), and print as `Movie, frames: N`. When the movie's frames come from its directory, N SHALL be the number of image files the directory currently holds.

#### Scenario: Movie with three frames
- **WHEN** three frames have been added to a movie
- **THEN** `len(movie)` is 3 and printing the movie shows `Movie, frames: 3`

### Requirement: Write a single numbered frame
`writeFrame(num, directory, picture)` SHALL write `picture` to `directory` as a PNG named `frame` followed by `num` zero-padded to 4 digits (`frame0007.png` for `num` 7). Numbers above 9999 SHALL be written without padding. The directory SHALL be created if it does not exist. An existing file of the same name SHALL be overwritten.

#### Scenario: Write frame 7
- **WHEN** `writeFrame(7, "frames", picture)` is called
- **THEN** the file `frames/frame0007.png` exists and contains the picture

#### Scenario: Directory does not exist yet
- **WHEN** `writeFrame(1, "newdir", picture)` is called and `newdir` does not exist
- **THEN** `newdir` is created and `newdir/frame0001.png` is written

#### Scenario: Invalid frame number
- **WHEN** `writeFrame(-1, "frames", picture)` or `writeFrame("one", "frames", picture)` is called
- **THEN** the error convention applies

#### Scenario: Third argument is not a Picture
- **WHEN** `writeFrame(1, "frames", "picture.png")` is called
- **THEN** the error convention applies

### Requirement: Write all frames to a directory
`writeFramesToDirectory(movie, directory=None)` SHALL write every frame of the movie, in order, to `directory` as `frame0001.png`, `frame0002.png`, and so on. When `directory` is omitted, it SHALL be the current working directory. The directory SHALL be created if it does not exist, and files of the same name SHALL be overwritten. Afterwards, the movie's directory SHALL be set to that directory.

#### Scenario: Write a three-frame movie
- **WHEN** `writeFramesToDirectory(movie, "out")` is called on a movie with three frames
- **THEN** `out/frame0001.png`, `out/frame0002.png` and `out/frame0003.png` exist, holding the frames in order
- **AND** the movie's directory is the resolved `out` path

#### Scenario: No directory given
- **WHEN** `writeFramesToDirectory(movie)` is called
- **THEN** the frames are written to the current working directory, even if a media folder is set

#### Scenario: Input is not a movie
- **WHEN** `writeFramesToDirectory("movie")` is called
- **THEN** the error convention applies

#### Scenario: Movie has no frames
- **WHEN** `writeFramesToDirectory(makeMovie(), "out")` is called
- **THEN** the error convention applies
