# Movies with mediaComp

`mediaCompMovie.py` adds movies to mediaComp: you can build an animation
frame by frame, play it in a window, and save it as a video file.

**Movie Functions.pdf**, next to `mediaCompMovie.py`, describes every movie
function with an example. This page shows how to get started.

## Setting up (Windows and Thonny)

1. In Thonny, open **Tools → Manage packages**, search for `mediaComp`, and
   install it (you may already have it).
2. Copy `mediaCompMovie.py` into the **same folder as your program**.
3. Start your program with these two lines:

```python
from mediaComp import *
from mediaCompMovie import *
```

That is all you need to make and play movies. Saving movies as video files
needs two more packages; see [Saving a video file](#saving-a-video-file).

## Example: a moving rectangle

Each pass through the loop draws one frame and adds it to the movie.

```python
from mediaComp import *
from mediaCompMovie import *

def makeRectMovie():
    movie = makeMovie()
    for num in range(1, 30):
        canvas = makeEmptyPicture(300, 200)
        addRectFilled(canvas, num * 10, num * 5, 50, 50, red)
        addFrameToMovie(canvas, movie)
    return movie

movie = makeRectMovie()
print(movie)
playMovie(movie)
```

`print(movie)` shows `Movie, frames: 29`. `playMovie` opens a window that
plays the movie over and over, 16 frames a second, until you close it. Your
program carries on while the movie plays.

## Example: writing frames to a folder

You can also save each frame as an image file with `writeFrame`, then make a
movie from the folder. The frames are named `frame0001.png`,
`frame0002.png`, and so on.

```python
from mediaComp import *
from mediaCompMovie import *

def makeBallFrames(directory):
    for num in range(1, 31):
        canvas = makeEmptyPicture(300, 200)
        addOvalFilled(canvas, num * 8, 80, 40, 40, blue)
        writeFrame(num, directory, canvas)

makeBallFrames("frames")
movie = makeMovie("frames")
playMovie(movie)
```

## The playback window

| Key | What it does |
|---|---|
| Space | Pause or resume. The title says `(paused)`. |
| Right / left arrow | While paused, go one frame forward or back. |
| Escape | Close the window (the same as its X button). |

The title shows which frame is on screen, for example `Movie: frame 3 of 29`.

Your program carries on while the movie plays, and the window closes when
you press Stop in Thonny. To make your program wait until the window is
closed, use `playMovie(movie, True)`. Do that to watch several movies one
after another, or when you run your program outside Thonny: there, the
window closes as soon as your program ends.

Movies always play at 16 frames per second. To choose a speed, save the
movie as a video file with the speed you want (see below).

## Where files go

A file or folder name without a drive or full path, such as `"frames"`, is
looked for in your **media folder** if you have set one with
`setMediaFolder()`. Otherwise it is looked for in the folder Thonny runs your
program from, which is normally your program's folder. One exception:
`writeFramesToDirectory(movie)` with no folder always writes to that current
folder.

## Saving a video file

To save videos, install `imageio` and `imageio-ffmpeg` with
**Tools → Manage packages** in Thonny. Without them, the save functions
print:

```
Movie export needs: pip install imageio imageio-ffmpeg (Thonny: Tools → Manage packages)
```

Then:

```python
writeMP4(movie, "anim.mp4")          # 16 frames per second
writeAVI(movie, "anim.avi", 30)      # 30 frames per second
writeQuicktime(movie, "anim.mov")
writeMovie(movie, "anim")            # MP4, unless you call setMovieFormat
```

The files play in Windows' own video player. All the frames of a movie must
be the same size to save it as a video.

## Function reference

See **Movie Functions.pdf** for what each function does, its inputs, and an
example. Inputs in `[ ]` are optional.

- `addFrameToMovie(frame, movie)`
- `getMovieFormat()`
- `makeMovie([directory])`
- `makeMovieFromInitialFile(filename)`
- `playMovie(movie[, isBlocking])`
- `setMovieFormat(fmt)`
- `writeAVI(movie, path[, framesPerSec])`
- `writeFrame(num, directory, picture)`
- `writeFramesToDirectory(movie[, directory])`
- `writeMovie(movie, path[, framesPerSec])`
- `writeMP4(movie, path[, framesPerSec])`
- `writeQuicktime(movie, path[, framesPerSec])`

The start of the Movie Functions section in the PDF also covers things to
watch out for: old frame files left in a folder, and memory use.

## Rebuilding the reference (developers)

`Movie Functions.docx` and `Movie Functions.pdf` are generated from
`docs/movie-functions.md`; edit that file, never the generated ones. In WSL
or Linux, install the tools once:

```
sudo apt install libreoffice-writer-nogui python3-uno \
                 fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea
venv/bin/pip install -r contrib/movie/requirements-dev.txt
```

Then, from the repository root, run `venv/bin/python contrib/movie/docs/build.py`
(add `--no-pdf` to skip LibreOffice). `tests/movie/test_reference_doc.py`
checks that the source matches the functions in `mediaCompMovie.py`.
