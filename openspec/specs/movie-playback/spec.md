# movie-playback Specification

## Purpose

Lets students watch their movies in a window from Thonny on Windows, at a fixed 16 frames per second, with the script either waiting for the window or carrying on, and with the window always closing cleanly.

## Requirements

### Requirement: Play a movie in a window
`playMovie(movie)` SHALL open a window that shows the movie's frames in order and loops back to the first frame after the last, until the window is closed. Playback SHALL work with only mediaComp and its own dependencies installed; it SHALL NOT need the optional export packages.

#### Scenario: Play a movie
- **WHEN** `playMovie(movie)` is called on a movie with 20 frames
- **THEN** a window opens and shows frames 1 to 20 repeatedly until it is closed

#### Scenario: Export packages not installed
- **WHEN** `playMovie(movie)` is called and the optional export packages are not installed
- **THEN** the movie plays normally

### Requirement: Fixed playback speed
Playback SHALL always run at 16 frames per second, the JES default. `playMovie` SHALL NOT take a speed argument, positional or keyword: the frame rate of a movie is chosen only when it is written to a video file.

#### Scenario: Fixed speed
- **WHEN** `playMovie(movie)` is called
- **THEN** frames advance at 16 frames per second

#### Scenario: Old speed keywords are not accepted
- **WHEN** `playMovie(movie, framesPerSec=30)` or `playMovie(movie, delay=0.1)` is called
- **THEN** Python raises a `TypeError` for the unexpected keyword and no window opens

#### Scenario: Speed is chosen when saving
- **WHEN** a student wants a movie to run at 30 frames per second
- **THEN** they pass 30 as the optional last argument of `writeMovie`, `writeMP4`, `writeAVI` or `writeQuicktime`, and the saved video runs at that rate

### Requirement: Playback input validation
`playMovie` SHALL apply the error convention, without opening a window, when its first argument is not a movie or the movie has no frames.

#### Scenario: Not a movie
- **WHEN** `playMovie("frames")` is called
- **THEN** the error convention applies and no window opens

#### Scenario: Empty movie
- **WHEN** `playMovie(makeMovie())` is called
- **THEN** the error convention applies and no window opens

#### Scenario: Directory movie with no images
- **WHEN** `playMovie(makeMovie("emptydir"))` is called and `emptydir` holds no image files
- **THEN** the error convention applies and no window opens

### Requirement: Optional blocking argument
The signature SHALL be `playMovie(movie[, isBlocking])`, with `isBlocking` an optional positional argument that defaults to `False`, matching mediaComp's `play(sound[, isBlocking])`. `isBlocking` SHALL be interpreted as `play()` interprets it: any true value makes the call block, and any false value makes it non-blocking. No value SHALL be rejected. A blocking call SHALL return only after the playback window is closed. A non-blocking call SHALL return as soon as the window has been started, and the script SHALL carry on while the movie plays. There SHALL be no module-level blocking setting and no `setPlayBlocking` or `getPlayBlocking` function.

#### Scenario: Default non-blocking
- **WHEN** a script calls `playMovie(movie)` and then `print("done")`
- **THEN** `done` is printed while the window is still playing

#### Scenario: Blocking
- **WHEN** a script calls `playMovie(movie, True)` and then `print("done")`
- **THEN** `done` is printed only after the playback window is closed

#### Scenario: Truthy value blocks
- **WHEN** `playMovie(movie, 1)` is called
- **THEN** the call blocks, as `play(sound, 1)` would

#### Scenario: Falsy value does not block
- **WHEN** `playMovie(movie, 0)` is called
- **THEN** the call does not block

#### Scenario: Old Guzdial delay argument
- **WHEN** an older script calls `playMovie(movie, 0.1)`
- **THEN** the value is treated as a true `isBlocking`, so the call blocks and the movie plays at 16 frames per second

#### Scenario: Old blocking keyword is gone
- **WHEN** a script calls `playMovie(movie, block=True)`
- **THEN** Python raises a `TypeError` for the unexpected keyword and no window opens

#### Scenario: Blocking setters are gone
- **WHEN** a script that used `from mediaCompMovie import *` refers to `setPlayBlocking` or `getPlayBlocking`
- **THEN** Python raises a `NameError`

#### Scenario: Several movies at once
- **WHEN** a script calls `playMovie(a)` and then `playMovie(b)`
- **THEN** two playback windows are open and playing at the same time

### Requirement: Frames reflect the movie at the time of the call
The playback window SHALL show the movie's frames as they were when `playMovie` was called. Changes to the movie after the call SHALL NOT affect a window that is already playing.

#### Scenario: Movie changed during non-blocking playback
- **WHEN** a script calls `playMovie(movie)` and then adds frames to `movie`
- **THEN** the open window keeps playing the frames the movie had at the time of the call

### Requirement: Mixed frame sizes in playback
Playback SHALL accept frames of different sizes. The window SHALL be large enough for the largest frame, and each frame SHALL be shown unscaled.

#### Scenario: Two frame sizes
- **WHEN** a movie holds frames of 200x100 and 300x150 and is played
- **THEN** the window is at least 300x150 and both frames are shown at their own size

### Requirement: Player window title and controls
The playback window title SHALL show the current frame number and the total frame count. The space bar SHALL pause and resume playback. While paused, the left and right arrow keys SHALL step one frame back or forward, wrapping around at either end. The Escape key SHALL close the window as if its close button had been pressed. The title SHALL show when playback is paused.

#### Scenario: Title during playback
- **WHEN** frame 3 of 20 is on screen
- **THEN** the window title includes `3` and `20`

#### Scenario: Pause and step
- **WHEN** the user presses space and then the right arrow
- **THEN** playback stops, the title shows it is paused, and the next frame is shown

#### Scenario: Step back past the first frame
- **WHEN** playback is paused on frame 1 and the user presses the left arrow
- **THEN** the last frame is shown

#### Scenario: Escape
- **WHEN** the user presses Escape
- **THEN** the window closes, and a blocking `playMovie` call returns

### Requirement: Clean shutdown
A playback window SHALL never outlive the Python process that started it. If a blocking call is interrupted (for example by Ctrl+C or Thonny's Stop button), its window SHALL close and the interruption SHALL reach the script. When the Python process that started a non-blocking window exits or is stopped, including through Thonny's Stop/Restart, the window SHALL close. Temporary files created for playback SHALL be removed when the window closes.

#### Scenario: Interrupt during blocking playback
- **WHEN** a script is blocked in `playMovie` and is interrupted
- **THEN** the window closes and the script stops with the interruption

#### Scenario: Thonny Stop/Restart with a non-blocking window open
- **WHEN** a non-blocking window is playing and Thonny's Stop/Restart is used
- **THEN** the window closes, and no player process remains running

#### Scenario: Temporary frames cleaned up
- **WHEN** a movie made from `Picture` frames is played and the window is then closed
- **THEN** no temporary frame files from that playback remain

#### Scenario: Re-running a script while a window is open
- **WHEN** a script with a non-blocking `playMovie` is run again in Thonny while the previous window is still open
- **THEN** the old window closes when Thonny restarts the backend, and the new run opens a new window
