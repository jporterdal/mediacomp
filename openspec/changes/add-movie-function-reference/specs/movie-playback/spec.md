## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Frames reflect the movie at the time of the call
The playback window SHALL show the movie's frames as they were when `playMovie` was called. Changes to the movie after the call SHALL NOT affect a window that is already playing.

#### Scenario: Movie changed during non-blocking playback
- **WHEN** a script calls `playMovie(movie)` and then adds frames to `movie`
- **THEN** the open window keeps playing the frames the movie had at the time of the call

## REMOVED Requirements

### Requirement: Playback speed
**Reason**: `playMovie` was the only movie function that needed keyword arguments (`framesPerSec=`), and Guzdial's `delay` used a different unit (seconds per frame) from the `framesPerSec` of the write functions. JES's own `playMovie(movie)` had no speed parameter. Replaced by "Fixed playback speed".
**Migration**: Remove the speed argument from `playMovie` calls. Choose the frame rate when saving, for example `writeMP4(movie, "anim.mp4", 30)`.

### Requirement: Blocking and non-blocking playback
**Reason**: Replaced by "Optional blocking argument". Blocking is now an optional positional `isBlocking` that defaults to `False`, matching mediaComp's `play(sound[, isBlocking])`, instead of a `block=` keyword with a module-level default.
**Migration**:
- Replace `playMovie(movie, block=True)` with `playMovie(movie, True)`.
- Replace `playMovie(movie, block=False)` with `playMovie(movie)`.
- Delete calls to `setPlayBlocking` and `getPlayBlocking`.
- A script that relied on the old blocking default must now pass `True`.
