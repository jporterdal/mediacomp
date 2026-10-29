"""Movie support for mediaComp: build, play and save animations.

Put this file next to your script and import it after mediaComp:

    from mediaComp import *
    from mediaCompMovie import *

The file has three sections, each of which will become its own file when
movie support moves into the mediaComp package:

    A. Movie             -> mediaComp/models/Movie.py
    B. wrapper functions -> mediaComp/core/movie.py
    C. player            -> mediaComp/scripts/moviePlayer.py

Run as a script with ``--play <manifest.json>``, it is the playback window
that playMovie() starts in a subprocess.
"""

import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

from mediaComp import getMediaFolder
from mediaComp.models.Picture import Picture
import PIL.Image

__all__ = [
    "makeMovie", "makeMovieFromInitialFile", "addFrameToMovie", "writeFrame",
    "writeFramesToDirectory", "playMovie", "setPlayBlocking", "getPlayBlocking",
    "writeMovie", "writeMP4", "writeAVI", "writeQuicktime",
    "setMovieFormat", "getMovieFormat",
]


# ---------------------------------------------------------------------------
# Section A: Movie (future mediaComp/models/Movie.py)
# ---------------------------------------------------------------------------

_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")
_PNG_MODES = ("1", "L", "LA", "P", "RGB", "RGBA")


def _frameSortKey(name):
    """Sort key that compares the digit runs in a file name as numbers."""
    name = os.path.basename(name)
    parts = re.split(r"(\d+)", name)
    return ([int(part) if i % 2 else part for i, part in enumerate(parts)], name)


def _scanDirectory(directory):
    """Return the image files in directory as absolute paths, in frame order."""
    if not os.path.isdir(directory):
        return []
    names = [name for name in os.listdir(directory)
             if os.path.splitext(name)[1].lower() in _IMAGE_EXTENSIONS
             and os.path.isfile(os.path.join(directory, name))]
    names.sort(key=_frameSortKey)
    return [os.path.abspath(os.path.join(directory, name)) for name in names]


def _loadImage(entry):
    """Return a frame (a path or a PIL snapshot) as a fully loaded PIL image."""
    if isinstance(entry, PIL.Image.Image):
        return entry
    image = PIL.Image.open(entry)
    image.load()
    return image


def _saveFramePNG(entry, path):
    """Write a frame (a path or a PIL snapshot) to path as a PNG."""
    image = _loadImage(entry)
    if image.mode not in _PNG_MODES:
        image = image.convert("RGBA")
    image.save(path, format="PNG")


class Movie:
    """A sequence of frames, each an image file path or a picture snapshot.

    If no frames have been added but dir is set, the frames are the image
    files in dir at the moment they are needed.
    """

    def __init__(self, directory=None):
        self.frames = []
        self.dir = directory

    def addFrame(self, frame):
        self.frames.append(frame)

    def resolvedFrames(self):
        if self.frames:
            return list(self.frames)
        if self.dir is None:
            return []
        return _scanDirectory(self.dir)

    def __len__(self):
        return len(self.resolvedFrames())

    def __getitem__(self, index):
        return self.resolvedFrames()[index]

    def __str__(self):
        return "Movie, frames: " + str(len(self))

    __repr__ = __str__


# ---------------------------------------------------------------------------
# Section B: wrapper functions (future mediaComp/core/movie.py)
# ---------------------------------------------------------------------------

def _fail(signature, message):
    """Report invalid input the way mediaComp does: print, then ValueError."""
    print(signature + ": " + message)
    raise ValueError(message)


def _resolve(path):
    """Resolve a relative path against the media folder (or the cwd if unset).

    mediaComp's own makePicture/writePictureTo cannot be used with relative
    paths (they refer to an undefined global mediaFolder), so all movie file
    access goes through here and then PIL directly.
    """
    if os.path.isabs(path):
        return path
    return os.path.abspath(getMediaFolder(path))


def _frameName(num):
    return "frame%04d.png" % num


def makeMovie(directory=None):
    """
    Makes a new movie. With no input the movie is empty; add frames with
    addFrameToMovie. With a directory, the movie's frames are the image files
    in that directory (in frame-number order) at the time it is played or saved.

    :param directory: (optional) the folder that holds or will hold the frames
    :return: the new movie
    """
    if directory is None:
        return Movie()
    if not isinstance(directory, str):
        _fail("makeMovie([directory])", "Input is not a directory name")
    return Movie(_resolve(directory))


def makeMovieFromInitialFile(filename):
    """
    Makes a movie from a numbered sequence of image files, such as
    frame0001.png, frame0002.png, ... Every file in the same folder whose name
    matches filename apart from its numbers becomes a frame, in number order.

    :param filename: the first frame file, for example "frames/frame0001.png"
    :return: the new movie
    """
    signature = "makeMovieFromInitialFile(filename)"
    if not isinstance(filename, str):
        _fail(signature, "Input is not a file name")
    path = _resolve(filename)
    if not os.path.isfile(path):
        _fail(signature, "There is no file at " + path)
    directory, name = os.path.split(path)
    pattern = re.compile("".join(
        r"\d+" if i % 2 else re.escape(part)
        for i, part in enumerate(re.split(r"(\d+)", name))))
    names = [other for other in os.listdir(directory)
             if pattern.fullmatch(other)
             and os.path.isfile(os.path.join(directory, other))]
    names.sort(key=_frameSortKey)
    movie = Movie()
    for other in names:
        movie.addFrame(os.path.join(directory, other))
    return movie


def addFrameToMovie(frame, movie):
    """
    Adds one frame to the end of a movie. The inputs may be given in either
    order. A picture is copied as it looks now, so you can keep drawing on the
    same picture and add it again for the next frame.

    :param frame: a picture, or the name of an image file
    :param movie: the movie to add the frame to
    """
    signature = "addFrameToMovie(frame, movie)"
    if isinstance(frame, Movie) and not isinstance(movie, Movie):
        frame, movie = movie, frame
    if not isinstance(movie, Movie):
        _fail(signature, "Neither input is a movie")
    if isinstance(frame, Picture):
        movie.addFrame(frame.getImage().copy())
    elif isinstance(frame, str):
        path = _resolve(frame)
        if not os.path.isfile(path):
            _fail(signature, "There is no file at " + path)
        movie.addFrame(path)
    else:
        _fail(signature, "Frame is not a picture or a file name")


def writeFrame(num, directory, picture):
    """
    Saves a picture as one numbered frame, frame0001.png for num 1, in a
    directory (created if needed). Use makeMovie(directory) to play the frames.

    :param num: the frame number, a whole number 0 or greater
    :param directory: the folder to save the frame in
    :param picture: the picture to save
    """
    signature = "writeFrame(num, directory, picture)"
    if isinstance(num, bool) or not isinstance(num, int) or num < 0:
        _fail(signature, "Frame number must be a whole number 0 or greater")
    if not isinstance(directory, str):
        _fail(signature, "Directory is not a directory name")
    if not isinstance(picture, Picture):
        _fail(signature, "Third input is not a picture")
    path = _resolve(directory)
    os.makedirs(path, exist_ok=True)
    _saveFramePNG(picture.getImage(), os.path.join(path, _frameName(num)))


def writeFramesToDirectory(movie, directory=None):
    """
    Saves every frame of a movie as frame0001.png, frame0002.png, ... in a
    directory (created if needed). Files already there with the same names are
    replaced; other files are left alone.

    :param movie: the movie to save
    :param directory: (optional) the folder to save to; the current folder if
                      not given
    """
    signature = "writeFramesToDirectory(movie[, directory])"
    if not isinstance(movie, Movie):
        _fail(signature, "First input is not a movie")
    if directory is None:
        path = os.getcwd()
    elif not isinstance(directory, str):
        _fail(signature, "Directory is not a directory name")
    else:
        path = _resolve(directory)
    frames = movie.resolvedFrames()
    if not frames:
        _fail(signature, "Movie has no frames")
    os.makedirs(path, exist_ok=True)
    for num, entry in enumerate(frames, 1):
        _saveFramePNG(entry, os.path.join(path, _frameName(num)))
    movie.dir = path


DEFAULT_PLAY_BLOCKING = True

# Non-blocking players. Holding the Popen keeps its stdin pipe open; letting
# it be garbage-collected would close the pipe and stop the player early.
_players = []


def _isPositiveNumber(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0)


def _stopPlayer(proc):
    """Close the player's stdin so it quits, and terminate it if it does not."""
    try:
        proc.stdin.close()
    except OSError:
        pass
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait()


def setPlayBlocking(flag):
    """
    Sets whether playMovie waits for its window to be closed (True, the
    starting setting) or lets your program carry on while the movie plays
    (False).

    :param flag: True or False
    """
    global DEFAULT_PLAY_BLOCKING
    if not isinstance(flag, bool):
        _fail("setPlayBlocking(flag)", "Input must be True or False")
    DEFAULT_PLAY_BLOCKING = flag


def getPlayBlocking():
    """
    Tells you whether playMovie waits for its window to be closed.

    :return: True or False
    """
    return DEFAULT_PLAY_BLOCKING


def playMovie(movie, delay=None, framesPerSec=None, block=None):
    """
    Plays a movie in a window, over and over, until the window is closed.
    Space pauses; while paused, the left and right arrows step a frame;
    Escape closes the window. Plays 16 frames per second unless you give
    delay or framesPerSec (not both).

    :param movie: the movie to play
    :param delay: (optional) seconds to show each frame, for example 0.1
    :param framesPerSec: (optional) frames per second, for example 30
    :param block: (optional) True to wait for the window to close, False to
                  carry on while it plays; the default is set by setPlayBlocking
    """
    signature = "playMovie(movie[, delay][, framesPerSec=n][, block=flag])"
    if not isinstance(movie, Movie):
        _fail(signature, "First input is not a movie")
    if delay is not None and framesPerSec is not None:
        _fail(signature, "Give either delay or framesPerSec, not both")
    if delay is not None:
        if not _isPositiveNumber(delay):
            _fail(signature, "delay must be a number of seconds greater than 0")
        fps = 1.0 / delay
    elif framesPerSec is not None:
        if not _isPositiveNumber(framesPerSec):
            _fail(signature, "framesPerSec must be a number greater than 0")
        fps = framesPerSec
    else:
        fps = 16
    if block is None:
        block = DEFAULT_PLAY_BLOCKING
    elif not isinstance(block, bool):
        _fail(signature, "block must be True or False")
    frames = movie.resolvedFrames()
    if not frames:
        _fail(signature, "Movie has no frames")

    # Copy every frame, so the window shows the movie as it is right now.
    tempdir = tempfile.mkdtemp(prefix="mediaCompMovie-")
    try:
        paths = []
        for num, entry in enumerate(frames, 1):
            path = os.path.join(tempdir, "%04d.png" % num)
            _saveFramePNG(entry, path)
            paths.append(path)
        manifest = os.path.join(tempdir, "manifest.json")
        with open(manifest, "w") as f:
            json.dump({"frames": paths, "fps": fps, "tempdir": tempdir}, f)
        options = {}
        if sys.platform == "win32":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        proc = subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "--play", manifest],
            stdin=subprocess.PIPE,
            env=dict(os.environ, PYGAME_HIDE_SUPPORT_PROMPT="1"),
            **options)
    except BaseException:
        shutil.rmtree(tempdir, ignore_errors=True)
        raise

    if not block:
        for old in [p for p in _players if p.poll() is not None]:
            old.stdin.close()
            _players.remove(old)
        _players.append(proc)
        return
    try:
        proc.wait()
    finally:
        _stopPlayer(proc)
        shutil.rmtree(tempdir, ignore_errors=True)


DEFAULT_MOVIE_FORMAT = "mp4"

_FORMATS = ("mp4", "avi", "mov")
_SUPPORTED = "Supported formats are mp4, avi and mov"
# codec, pixel format, extra ffmpeg options. MJPEG is used for AVI because
# H.264 in AVI often fails to play in the Windows player.
_ENCODERS = {
    "mp4": ("libx264", "yuv420p", {}),
    "mov": ("libx264", "yuv420p", {}),
    "avi": ("mjpeg", "yuvj420p", {"quality": None, "output_params": ["-q:v", "3"]}),
}
_EXPORT_HINT = ("Movie export needs: pip install imageio imageio-ffmpeg "
                "(Thonny: Tools → Manage packages)")


def setMovieFormat(fmt):
    """
    Sets the video format writeMovie uses when the file name has no
    extension. It starts as "mp4".

    :param fmt: "mp4", "avi" or "mov"
    """
    global DEFAULT_MOVIE_FORMAT
    name = fmt.lower().lstrip(".") if isinstance(fmt, str) else None
    if name not in _FORMATS:
        _fail("setMovieFormat(format)", _SUPPORTED)
    DEFAULT_MOVIE_FORMAT = name


def getMovieFormat():
    """
    Tells you the video format writeMovie uses when the file name has no
    extension.

    :return: "mp4", "avi" or "mov"
    """
    return DEFAULT_MOVIE_FORMAT


def _frameSize(entry):
    if isinstance(entry, PIL.Image.Image):
        return entry.size
    with PIL.Image.open(entry) as image:
        return image.size


def _export(signature, movie, path, fps, fmt):
    """Write movie to a video file. fmt None means: choose from the extension."""
    if not isinstance(movie, Movie):
        _fail(signature, "First input is not a movie")
    if not isinstance(path, str):
        _fail(signature, "Path is not a file name")
    if not _isPositiveNumber(fps):
        _fail(signature, "framesPerSec must be a number greater than 0")
    if fmt is None:
        extension = os.path.splitext(path)[1].lower()
        if not extension:
            fmt = DEFAULT_MOVIE_FORMAT
        elif extension[1:] in _FORMATS:
            fmt = extension[1:]
        else:
            _fail(signature, "Cannot write " + extension + " files. " + _SUPPORTED)
    if not path.lower().endswith("." + fmt):
        path += "." + fmt
    path = _resolve(path)
    frames = movie.resolvedFrames()
    if not frames:
        _fail(signature, "Movie has no frames")

    try:
        import imageio.v2 as imageio
        import imageio_ffmpeg  # noqa: F401  (provides the ffmpeg binary)
    except ImportError:
        print(_EXPORT_HINT)
        raise ValueError(_EXPORT_HINT)
    import numpy as np

    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        _fail(signature, "There is no folder at " + folder)
    width, height = _frameSize(frames[0])
    for num, entry in enumerate(frames[1:], 2):
        size = _frameSize(entry)
        if size != (width, height):
            _fail(signature, "Frame %d is %dx%d but frame 1 is %dx%d. "
                  "All frames must be the same size"
                  % (num, size[0], size[1], width, height))

    codec, pixelformat, options = _ENCODERS[fmt]
    padding = ((0, height % 2), (0, width % 2), (0, 0))
    writer = imageio.get_writer(path, format="FFMPEG", fps=fps, codec=codec,
                                pixelformat=pixelformat, macro_block_size=1,
                                ffmpeg_log_level="error", **options)
    try:
        for entry in frames:
            pixels = np.asarray(_loadImage(entry).convert("RGB"))
            if height % 2 or width % 2:
                pixels = np.pad(pixels, padding, mode="edge")
            writer.append_data(pixels)
        writer.close()
    except BaseException:
        try:
            writer.close()
        except Exception:
            pass
        if os.path.exists(path):
            os.remove(path)
        raise


def writeMovie(movie, path, framesPerSec=16):
    """
    Saves a movie as a video file. The format comes from the file name's
    extension (.mp4, .avi or .mov); with no extension, the format set by
    setMovieFormat is used and its extension added. All frames must be the
    same size. Needs: pip install imageio imageio-ffmpeg

    :param movie: the movie to save
    :param path: the video file name, for example "anim.mp4"
    :param framesPerSec: (optional) frames per second; 16 if not given
    """
    _export("writeMovie(movie, path[, framesPerSec])", movie, path, framesPerSec, None)


def writeMP4(movie, path, framesPerSec=16):
    """
    Saves a movie as an MP4 video file, adding .mp4 to the name if it is not
    there. All frames must be the same size.
    Needs: pip install imageio imageio-ffmpeg

    :param movie: the movie to save
    :param path: the video file name, for example "anim.mp4"
    :param framesPerSec: (optional) frames per second; 16 if not given
    """
    _export("writeMP4(movie, path[, framesPerSec])", movie, path, framesPerSec, "mp4")


def writeAVI(movie, path, framesPerSec=16):
    """
    Saves a movie as an AVI video file, adding .avi to the name if it is not
    there. All frames must be the same size.
    Needs: pip install imageio imageio-ffmpeg

    :param movie: the movie to save
    :param path: the video file name, for example "anim.avi"
    :param framesPerSec: (optional) frames per second; 16 if not given
    """
    _export("writeAVI(movie, path[, framesPerSec])", movie, path, framesPerSec, "avi")


def writeQuicktime(movie, path, framesPerSec=16):
    """
    Saves a movie as a QuickTime (.mov) video file, adding .mov to the name
    if it is not there. All frames must be the same size.
    Needs: pip install imageio imageio-ffmpeg

    :param movie: the movie to save
    :param path: the video file name, for example "anim.mov"
    :param framesPerSec: (optional) frames per second; 16 if not given
    """
    _export("writeQuicktime(movie, path[, framesPerSec])", movie, path, framesPerSec, "mov")


# ---------------------------------------------------------------------------
# Section C: player (future mediaComp/scripts/moviePlayer.py)
# ---------------------------------------------------------------------------

def _watchStdin(pygame):
    """Post a quit event once stdin reaches EOF, i.e. the parent has gone."""
    def watch():
        # Read the raw descriptor: a thread blocked in sys.stdin.buffer.read
        # holds the buffer's lock, and Python aborts at shutdown if the window
        # was closed while the parent (and so stdin) is still alive.
        try:
            while os.read(sys.stdin.fileno(), 1024):
                pass
        except (OSError, ValueError):
            pass
        try:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        except pygame.error:
            pass
    threading.Thread(target=watch, daemon=True).start()


def _runPlayer(manifest, maxFrames=None, onTick=None, watchStdin=False):
    """Show the frames listed in a manifest file in a window, looping.

    The manifest is JSON: {"frames": [png paths], "fps": n, "tempdir": dir}.
    tempdir is removed when the window closes. maxFrames and onTick(tick)
    are test hooks: stop after that many frames are drawn, and call onTick
    at the top of each loop pass. Returns the window title of each frame
    drawn.
    """
    import pygame

    with open(manifest) as f:
        info = json.load(f)
    paths = info["frames"]
    fps = info["fps"]
    count = len(paths)
    titles = []
    try:
        sizes = []
        for path in paths:
            with PIL.Image.open(path) as image:
                sizes.append(image.size)
        width = max(size[0] for size in sizes)
        height = max(size[1] for size in sizes)

        pygame.display.init()
        screen = pygame.display.set_mode((width, height))
        if watchStdin:
            _watchStdin(pygame)

        surfaces = {}
        clock = pygame.time.Clock()
        index = 0
        paused = False
        ticks = 0
        running = True
        while running:
            if onTick is not None:
                onTick(ticks)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif paused and event.key == pygame.K_RIGHT:
                        index = (index + 1) % count
                    elif paused and event.key == pygame.K_LEFT:
                        index = (index - 1) % count
            if not running:
                break

            if index not in surfaces:
                surfaces[index] = pygame.image.load(paths[index]).convert()
            frame = surfaces[index]
            screen.fill((0, 0, 0))
            screen.blit(frame, ((width - frame.get_width()) // 2,
                                (height - frame.get_height()) // 2))
            title = "Movie: frame %d of %d" % (index + 1, count)
            if paused:
                title += " (paused)"
            pygame.display.set_caption(title)
            pygame.display.flip()
            titles.append(title)

            ticks += 1
            if maxFrames is not None and ticks >= maxFrames:
                break
            clock.tick(fps)
            if not paused:
                index = (index + 1) % count
    finally:
        pygame.quit()
        if info.get("tempdir"):
            shutil.rmtree(info["tempdir"], ignore_errors=True)
    return titles


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--play":
        try:
            _runPlayer(sys.argv[2], watchStdin=True)
        except KeyboardInterrupt:
            # Ctrl+C in a terminal reaches the player too; the parent reports it.
            pass
    else:
        print("usage: mediaCompMovie.py --play <manifest.json>")
        sys.exit(2)
