# Movies with mediaComp

`mediaCompMovie.py` adds movies to mediaComp: you can build an animation
frame by frame, play it in a window, and save it as a video file.

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
plays the movie over and over until you close it. Your program waits at
`playMovie` until then.

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
playMovie(movie, 0.1)
```

`playMovie(movie, 0.1)` shows each frame for 0.1 seconds.

## The playback window

| Key | What it does |
|---|---|
| Space | Pause or resume. The title says `(paused)`. |
| Right / left arrow | While paused, go one frame forward or back. |
| Escape | Close the window (the same as its X button). |

The title shows which frame is on screen, for example `Movie: frame 3 of 29`.

To let your program carry on while the movie plays, use
`playMovie(movie, block=False)`, or call `setPlayBlocking(False)` once at
the start. The window closes when you press Stop in Thonny.

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

| Function | What it does |
|---|---|
| `makeMovie()` | Makes a new, empty movie. |
| `makeMovie(directory)` | Makes a movie whose frames are the images in `directory`, in number order, at the time it is played or saved. |
| `makeMovieFromInitialFile(filename)` | Makes a movie from numbered files such as `frame0001.png`, `frame0002.png`… Give the first one. |
| `addFrameToMovie(frame, movie)` | Adds a picture, or the name of an image file, as the last frame. The picture is copied as it looks now. |
| `writeFrame(num, directory, picture)` | Saves `picture` as `frame0001.png` (for `num` 1) in `directory`, making the folder if needed. |
| `writeFramesToDirectory(movie, directory)` | Saves every frame as `frame0001.png`, `frame0002.png`… in `directory` (the current folder if left out). |
| `playMovie(movie)` | Plays the movie in a window at 16 frames per second. |
| `playMovie(movie, delay)` | Shows each frame for `delay` seconds. |
| `playMovie(movie, framesPerSec=n)` | Plays at `n` frames per second. |
| `playMovie(movie, block=False)` | Plays without making your program wait. |
| `setPlayBlocking(flag)` / `getPlayBlocking()` | Sets or tells whether `playMovie` waits (`True` to start with). |
| `writeMP4(movie, path, framesPerSec)` | Saves an MP4 video. `framesPerSec` is optional (16). |
| `writeAVI(movie, path, framesPerSec)` | Saves an AVI video. |
| `writeQuicktime(movie, path, framesPerSec)` | Saves a QuickTime (`.mov`) video. |
| `writeMovie(movie, path, framesPerSec)` | Saves a video in the format of the path's extension. |
| `setMovieFormat(fmt)` / `getMovieFormat()` | Sets or tells the format `writeMovie` uses when the path has no extension: `"mp4"` (to start with), `"avi"` or `"mov"`. |

## Things to watch out for

- **Old frame files.** `writeFrame` and `writeFramesToDirectory` replace
  files with the same names but leave other files alone. If an earlier run
  wrote 50 frames and this run writes 30, frames 31 to 50 are still in the
  folder, and `makeMovie(directory)` will include them. Delete the folder, or
  use a new one, before writing a shorter movie.
- **Memory.** Every picture you add with `addFrameToMovie` is kept in memory.
  A 640x480 frame takes about 1 MB, so 100 frames take about 100 MB. For very
  long movies, use smaller pictures or `writeFrame` to a folder instead.
