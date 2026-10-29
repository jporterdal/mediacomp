# movie-playback Specification

## Purpose

Lets students watch their movies in a window from Thonny on Windows, at a chosen speed, with the script either waiting for the window or carrying on, and with the window always closing cleanly.

## Requirements

### Requirement: Play a movie in a window
`playMovie(movie)` SHALL open a window that shows the movie's frames in order and loops back to the first frame after the last, until the window is closed. Playback SHALL work with only mediaComp and its own dependencies installed; it SHALL NOT need the optional export packages.

#### Scenario: Play a movie
- **WHEN** `playMovie(movie)` is called on a movie with 20 frames
- **THEN** a window opens and shows frames 1 to 20 repeatedly until it is closed

#### Scenario: Export packages not installed
- **WHEN** `playMovie(movie)` is called and the optional export packages are not installed
- **THEN** the movie plays normally

### Requirement: Playback speed
Playback SHALL default to 16 frames per second. The second positional argument, `delay`, SHALL set the time each frame is shown, in seconds (Guzdial style). The keyword `framesPerSec` SHALL set frames per second (JES style). Giving both SHALL be an error. A `delay` or `framesPerSec` that is not a positive number SHALL be an error.

#### Scenario: Default speed
- **WHEN** `playMovie(movie)` is called
- **THEN** frames advance at 16 frames per second

#### Scenario: Guzdial delay
- **WHEN** `playMovie(movie, 0.25)` is called
- **THEN** each frame is shown for about 0.25 seconds (4 frames per second)

#### Scenario: JES frames per second
- **WHEN** `playMovie(movie, framesPerSec=30)` is called
- **THEN** frames advance at 30 frames per second

#### Scenario: Both speeds given
- **WHEN** `playMovie(movie, 0.1, framesPerSec=30)` is called
- **THEN** the error convention applies

#### Scenario: Non-positive speed
- **WHEN** `playMovie(movie, 0)` or `playMovie(movie, framesPerSec=-5)` is called
- **THEN** the error convention applies

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

### Requirement: Blocking and non-blocking playback
By default, `playMovie` SHALL block: it returns only after the playback window is closed. A module-level setting `DEFAULT_PLAY_BLOCKING`, which starts as `True`, SHALL set the default for later calls. Students SHALL be able to change and read it with `setPlayBlocking(flag)` and `getPlayBlocking()`, which work after `from mediaCompMovie import *`, where assigning the name in the student's script would not. `setPlayBlocking` SHALL apply the error convention to a value that is not `True` or `False`. The keyword `block=True` or `block=False` on a single call SHALL override that setting. In non-blocking mode, `playMovie` SHALL return as soon as the window has been started, and the script SHALL carry on while the movie plays.

#### Scenario: Default blocking
- **WHEN** a script calls `playMovie(movie)` and then `print("done")`
- **THEN** `done` is printed only after the playback window is closed

#### Scenario: Per-call non-blocking
- **WHEN** a script calls `playMovie(movie, block=False)` and then `print("done")`
- **THEN** `done` is printed while the window is still playing

#### Scenario: Module-level default
- **WHEN** a script that used `from mediaCompMovie import *` calls `setPlayBlocking(False)` and then `playMovie(movie)`
- **THEN** the call does not block
- **AND** `getPlayBlocking()` returns `False`

#### Scenario: Per-call override of the default
- **WHEN** `setPlayBlocking(False)` has been called and a script calls `playMovie(movie, block=True)`
- **THEN** that call blocks

#### Scenario: Several movies at once
- **WHEN** a script calls `playMovie(a, block=False)` and then `playMovie(b, block=False)`
- **THEN** two playback windows are open and playing at the same time

### Requirement: Frames reflect the movie at the time of the call
The playback window SHALL show the movie's frames as they were when `playMovie` was called. Changes to the movie after the call SHALL NOT affect a window that is already playing.

#### Scenario: Movie changed during non-blocking playback
- **WHEN** a script calls `playMovie(movie, block=False)` and then adds frames to `movie`
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
