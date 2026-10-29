# Manual Windows + Thonny checklist for mediaCompMovie

Run these on a Windows 10 or 11 machine with Thonny, using mediaComp from
PyPI (>= 0.4.15) in Thonny's own interpreter. Record pass/fail and notes for
each item, and the Windows version and Thonny version used.

## Setup

1. In Thonny, **Tools → Manage packages**, install `mediaComp`. Do **not**
   install `imageio` or `imageio-ffmpeg` yet.
2. Make a folder, for example `C:\Users\<you>\Documents\movietest`, and copy
   `contrib/movie/mediaCompMovie.py` into it.
3. Save the script below in that folder as `check.py`. Each check edits only
   the last lines.

```python
from mediaComp import *
from mediaCompMovie import *

def rectMovie(count=20):
    movie = makeMovie()
    for num in range(1, count + 1):
        canvas = makeEmptyPicture(320, 240)
        addRectFilled(canvas, num * 12, num * 6, 40, 40, red)
        addText(canvas, 10, 20, "frame " + str(num), black)
        addFrameToMovie(canvas, movie)
    return movie

movie = rectMovie()
playMovie(movie)
print("done")
```

To list running players, open PowerShell and run:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*mediaCompMovie.py*--play*' } | Select-Object ProcessId, CommandLine
```

To list leftover playback temp folders:

```powershell
Get-ChildItem $env:TEMP -Filter 'mediaCompMovie-*'
```

## 1. Thonny with no export packages

| # | Steps | Expected |
|---|---|---|
| 1.1 | Run `check.py`. | No error on import. A window titled `Movie: frame i of 20` opens and loops through frames 1–20. No console window flashes up. `done` is **not** printed yet. |
| 1.2 | Note whether the window opened in front of Thonny and has focus (keys work without clicking it first). | Records the answer to design.md's window-focus open question. |
| 1.3 | Close the window with its X button. | `done` is printed. The PowerShell process list is empty. |
| 1.4 | Replace the last two lines with `writeMP4(movie, "anim.mp4")` and run. | Thonny prints `Movie export needs: pip install imageio imageio-ffmpeg (Thonny: Tools → Manage packages)` and a `ValueError`. No `anim.mp4` file is created. |

## 2. Playback speed and controls

| # | Steps | Expected |
|---|---|---|
| 2.1 | Run `check.py` and watch for a few loops. | About 16 frames a second: the 20 frames take a little over 1 second per loop. |
| 2.2 | Change the call to `playMovie(movie, 0.25)`. | Each frame stays about a quarter of a second (one loop takes about 5 seconds). |
| 2.3 | Change the call to `playMovie(movie, framesPerSec=4)`. | Same speed as 2.2. |
| 2.4 | Press space. | Playback stops; the title ends in `(paused)`. |
| 2.5 | While paused, press right arrow, then left arrow. | One frame forward, then one frame back; the title shows the frame number. |
| 2.6 | Step back with left arrow until frame 1, then press left once more. | Frame 20 is shown. |
| 2.7 | Press space again, then Escape. | Playback resumes; Escape closes the window and `done` is printed. |
| 2.8 | Make a movie with one 200x100 picture and one 300x150 picture and play it. | The window is 300x150; the small frame is centred, not stretched. |

## 3. Clean shutdown

These cover every scenario of the playback "Clean shutdown" requirement.

| # | Steps | Expected |
|---|---|---|
| 3.1 | **Interrupt during blocking playback.** Run `check.py`; while the window is playing, click Thonny's **Stop** button (or press Ctrl+C in the shell). | The window closes. The shell shows `KeyboardInterrupt` (or the backend restarts) and `done` is not printed. The process list is empty. |
| 3.2 | **Stop/Restart with a non-blocking window.** Change the call to `playMovie(movie, block=False)` and run. | `done` is printed while the window keeps playing. |
| 3.3 | With that window still open, click **Stop** (Stop/Restart backend). | The window closes within a couple of seconds. The process list is empty. |
| 3.4 | **Re-running with a window open.** Run the non-blocking script again, and while its window is open, press **F5** (run again). | The old window closes when Thonny restarts the backend, and one new window opens. The process list shows exactly one player. |
| 3.5 | **Script ends normally.** Add `import time; time.sleep(3)` after `print("done")` in the non-blocking script and run it. | The window plays for about 3 seconds, then closes when the script ends and Thonny's backend finishes. (If Thonny keeps the backend alive after the script, the window stays until Stop; record which.) |
| 3.6 | **Temporary frames cleaned up.** After 1.3, 2.7, 3.1, 3.3 and 3.4, run the temp-folder command. | No `mediaCompMovie-*` folders remain. |
| 3.7 | Run two players at once: `playMovie(movie, block=False)` twice. | Two windows play at the same time. Stop closes both. |

## 4. `show()` and `playMovie` together

| # | Steps | Expected |
|---|---|---|
| 4.1 | Before `playMovie(movie)`, add `show(makeEmptyPicture(100, 100, blue))`. | The picture window and the movie window both open and work. Closing the movie window returns; the picture window stays usable. |

## 5. Textbook and Guzdial-style scripts

| # | Steps | Expected |
|---|---|---|
| 5.1 | Run the moving-rectangle example from `contrib/movie/README.md` unchanged. | It plays as described there. |
| 5.2 | Run the Guzdial `writeFrame` example from the README unchanged. | A `frames` folder with `frame0001.png`… appears next to the script (or in the media folder, if one is set), and the movie plays. |
| 5.3 | Run `setMediaFolder()` and pick a folder whose path contains a space, then run 5.2 again. | The frames are written into that media folder and the movie plays. |
| 5.4 | Confirm that `sys.executable` (print it in Thonny's shell) is Thonny's backend Python, the one with mediaComp installed. | The player started from that interpreter: checks 1.1 and 5.1 worked. |

## 6. Export, with the export packages installed

Install `imageio` and `imageio-ffmpeg` with **Tools → Manage packages**
(or `pip install -r requirements-dev.txt` from `contrib/movie` in Thonny's
**Tools → Open system shell**).

| # | Steps | Expected |
|---|---|---|
| 6.1 | Replace the last lines with `writeMP4(movie, "anim.mp4")`, `writeAVI(movie, "anim.avi")`, `writeQuicktime(movie, "anim.mov")`. | Three non-empty files are created next to the script. |
| 6.2 | **Playable in Windows' built-in player.** Open each file by double-clicking it (Media Player on Windows 11, Movies & TV on Windows 10). Do not install any codecs. | Each one plays and shows frames 1–20 in order (the rectangle moves down-right, the frame number counts up). Record the AVI result for design.md's AVI codec open question. |
| 6.3 | Export again with `writeMP4(movie, "anim30.mp4", 30)` and open it. | Plays noticeably faster than `anim.mp4`. |
| 6.4 | Run `writeMovie(movie, "anim2")`. | `anim2.mp4` is created and plays. |
| 6.5 | Check that `playMovie(movie)` still works with the packages installed. | Same as 1.1. |

## 7. Automated Windows tests

| # | Steps | Expected |
|---|---|---|
| 7.1 | From a clone of the repo on Windows, with mediaComp installed in editable mode and `contrib/movie/requirements-dev.txt` installed, run `pytest -m windows`. | All Windows tests pass. |
| 7.2 | Run `pytest`. | Everything passes or is skipped; nothing fails. |

## Results

| Item | Result | Notes |
|---|---|---|
| Windows / Thonny version | | |
| Window focus (1.2) | | |
| AVI plays in built-in player (6.2) | | |
| Everything else | | |
