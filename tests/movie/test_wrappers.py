import os

import PIL.Image
import pytest
from mediaComp import addRectFilled, makeColor, makeEmptyPicture

import mediaCompMovie as mm

RED = (255, 0, 0)
BLUE = (0, 0, 255)


def _picture(rgb, size=(20, 10)):
    return makeEmptyPicture(size[0], size[1], makeColor(*rgb))


def _pixel(path, xy=(0, 0)):
    with PIL.Image.open(path) as image:
        return image.convert("RGB").getpixel(xy)


def _expectError(capsys, function, *args, contains=None):
    with pytest.raises(ValueError):
        function(*args)
    out = capsys.readouterr().out
    assert out.startswith(function.__name__ + "(")
    if contains is not None:
        assert contains in out
    return out


# makeMovie --------------------------------------------------------------

def test_make_empty_movie():
    movie = mm.makeMovie()
    assert len(movie) == 0
    assert movie.dir is None
    assert str(movie) == "Movie, frames: 0"


def test_make_directory_movie(cwd_tmp):
    movie = mm.makeMovie("frames")
    assert movie.dir == os.path.join(str(cwd_tmp), "frames")
    assert movie.frames == []
    assert len(movie) == 0


def test_directory_filled_after_creation(cwd_tmp, frames_factory):
    movie = mm.makeMovie("frames")
    paths = frames_factory(cwd_tmp / "frames", 3)
    assert len(movie) == 3
    assert movie.resolvedFrames() == paths


def test_added_frames_take_precedence_over_directory(cwd_tmp, frames_factory):
    frames_factory(cwd_tmp / "frames", 3)
    movie = mm.makeMovie("frames")
    mm.addFrameToMovie(_picture(RED), movie)
    assert len(movie) == 1


def test_make_movie_rejects_non_string_directory(capsys):
    _expectError(capsys, mm.makeMovie, 42)


# makeMovieFromInitialFile -----------------------------------------------

def test_initial_file_loads_50_frames(tmp_path, frames_factory):
    paths = frames_factory(tmp_path, 50)
    movie = mm.makeMovieFromInitialFile(paths[0])
    assert len(movie) == 50
    assert movie.resolvedFrames() == paths


def test_initial_file_loads_3_digit_names(tmp_path, frames_factory):
    paths = frames_factory(tmp_path, 12, pattern="frame{:03d}")
    assert len(mm.makeMovieFromInitialFile(paths[0])) == 12


def test_initial_file_excludes_unrelated_files(tmp_path, frames_factory):
    paths = frames_factory(tmp_path, 2)
    frames_factory(tmp_path, 1, ext="jpg")
    frames_factory(tmp_path, 1, pattern="background")
    frames_factory(tmp_path, 1, pattern="frameX")
    movie = mm.makeMovieFromInitialFile(paths[0])
    assert movie.resolvedFrames() == paths


def test_initial_file_missing(tmp_path, capsys):
    missing = str(tmp_path / "missing0001.png")
    _expectError(capsys, mm.makeMovieFromInitialFile, missing, contains=missing)


def test_initial_file_bare_name_uses_media_folder(tmp_media, cwd_tmp, frames_factory):
    paths = frames_factory(tmp_media, 5)
    movie = mm.makeMovieFromInitialFile("frame0001.png")
    assert movie.resolvedFrames() == paths


# addFrameToMovie --------------------------------------------------------

def test_add_path_frame(tmp_path, frames_factory):
    path = frames_factory(tmp_path, 1)[0]
    movie = mm.makeMovie()
    mm.addFrameToMovie(path, movie)
    assert len(movie) == 1
    assert movie[-1] == path


def test_add_frame_arguments_reversed():
    movie = mm.makeMovie()
    mm.addFrameToMovie(movie, _picture(RED))
    assert len(movie) == 1


def test_add_picture_frame():
    movie = mm.makeMovie()
    mm.addFrameToMovie(_picture(RED), movie)
    mm.addFrameToMovie(_picture(BLUE), movie)
    assert len(movie) == 2


def test_picture_frames_are_snapshots():
    movie = mm.makeMovie()
    picture = _picture((255, 255, 255))
    addRectFilled(picture, 0, 0, 5, 5, makeColor(*RED))
    mm.addFrameToMovie(picture, movie)
    addRectFilled(picture, 0, 0, 5, 5, makeColor(*BLUE))
    mm.addFrameToMovie(picture, movie)
    assert movie[0].getpixel((1, 1)) == RED
    assert movie[1].getpixel((1, 1)) == BLUE


def test_add_missing_frame_file(tmp_path, capsys):
    missing = str(tmp_path / "nope.png")
    _expectError(capsys, mm.addFrameToMovie, missing, mm.makeMovie(), contains=missing)


def test_add_frame_neither_is_movie(capsys):
    _expectError(capsys, mm.addFrameToMovie, "a.png", "b.png")


def test_add_frame_neither_path_nor_picture(capsys):
    _expectError(capsys, mm.addFrameToMovie, 42, mm.makeMovie())


# writeFrame -------------------------------------------------------------

def test_write_frame_7(cwd_tmp):
    mm.writeFrame(7, "frames", _picture(RED))
    path = cwd_tmp / "frames" / "frame0007.png"
    assert path.is_file()
    assert _pixel(str(path)) == RED


def test_write_frame_above_9999_is_unpadded(cwd_tmp):
    mm.writeFrame(12345, "frames", _picture(RED))
    assert (cwd_tmp / "frames" / "frame12345.png").is_file()


def test_write_frame_creates_directory(cwd_tmp):
    mm.writeFrame(1, "newdir", _picture(RED))
    assert (cwd_tmp / "newdir" / "frame0001.png").is_file()


def test_write_frame_overwrites(cwd_tmp):
    mm.writeFrame(1, "frames", _picture(RED))
    mm.writeFrame(1, "frames", _picture(BLUE))
    assert _pixel(str(cwd_tmp / "frames" / "frame0001.png")) == BLUE


@pytest.mark.parametrize("num", [-1, "one", True, 1.5])
def test_write_frame_invalid_number(cwd_tmp, capsys, num):
    _expectError(capsys, mm.writeFrame, num, "frames", _picture(RED))
    assert not (cwd_tmp / "frames").exists()


def test_write_frame_needs_picture(cwd_tmp, capsys):
    _expectError(capsys, mm.writeFrame, 1, "frames", "picture.png")


def test_written_frames_resolve_in_numeric_order(cwd_tmp):
    for num in [3, 1, 2, 10, 9999, 10000]:
        mm.writeFrame(num, "frames", _picture(RED))
    names = [os.path.basename(p) for p in mm.makeMovie("frames").resolvedFrames()]
    assert names == ["frame0001.png", "frame0002.png", "frame0003.png",
                     "frame0010.png", "frame9999.png", "frame10000.png"]


# writeFramesToDirectory -------------------------------------------------

def test_write_frames_to_directory(cwd_tmp):
    colors = [RED, (0, 255, 0), BLUE]
    movie = mm.makeMovie()
    for rgb in colors:
        mm.addFrameToMovie(_picture(rgb), movie)
    mm.writeFramesToDirectory(movie, "out")
    out = cwd_tmp / "out"
    assert sorted(os.listdir(out)) == ["frame0001.png", "frame0002.png", "frame0003.png"]
    for num, rgb in enumerate(colors, 1):
        assert _pixel(str(out / ("frame%04d.png" % num))) == rgb
    assert movie.dir == str(out)


def test_write_frames_defaults_to_cwd_even_with_media_folder(tmp_media, cwd_tmp):
    movie = mm.makeMovie()
    mm.addFrameToMovie(_picture(RED), movie)
    mm.writeFramesToDirectory(movie)
    assert (cwd_tmp / "frame0001.png").is_file()
    assert not (tmp_media / "frame0001.png").exists()
    assert movie.dir == str(cwd_tmp)


def test_write_frames_from_path_frames(tmp_path, cwd_tmp, frames_factory):
    paths = frames_factory(tmp_path / "src", 2, ext="jpg", pattern="pic{:02d}")
    movie = mm.makeMovie()
    for path in paths:
        mm.addFrameToMovie(path, movie)
    mm.writeFramesToDirectory(movie, "out")
    assert sorted(os.listdir(cwd_tmp / "out")) == ["frame0001.png", "frame0002.png"]


def test_write_frames_needs_movie(capsys):
    _expectError(capsys, mm.writeFramesToDirectory, "movie")


def test_write_frames_of_empty_movie(cwd_tmp, capsys):
    _expectError(capsys, mm.writeFramesToDirectory, mm.makeMovie(), "out")
    assert not (cwd_tmp / "out").exists()
