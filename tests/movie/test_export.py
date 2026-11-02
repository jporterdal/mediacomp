"""Video export. Needs imageio and imageio-ffmpeg (contrib/movie/requirements-dev.txt)."""

import os

import pytest

pytest.importorskip("imageio_ffmpeg")
imageio = pytest.importorskip("imageio.v2")

from mediaComp import makeColor, makeEmptyPicture  # noqa: E402

import mediaCompMovie as mm  # noqa: E402


@pytest.fixture(autouse=True)
def reset_format():
    yield
    mm.DEFAULT_MOVIE_FORMAT = "mp4"


def _movie(count=8, size=(64, 48), sizes=None):
    movie = mm.makeMovie()
    for num in range(count):
        width, height = sizes[num] if sizes else size
        shade = min(255, 20 + num * 25)
        mm.addFrameToMovie(makeEmptyPicture(width, height, makeColor(shade, 0, 0)), movie)
    return movie


def _readBack(path):
    reader = imageio.get_reader(path, format="FFMPEG")
    try:
        meta = reader.get_meta_data()
        frames = [frame for frame in reader]
    finally:
        reader.close()
    return meta, frames


def _container(path):
    with open(path, "rb") as f:
        head = f.read(12)
    if head[:4] == b"RIFF" and head[8:12] == b"AVI ":
        return "avi"
    if head[4:8] == b"ftyp":
        return "mov" if head[8:12] == b"qt  " else "mp4"
    return None


def _expectError(capsys, function, *args, contains=()):
    with pytest.raises(ValueError):
        function(*args)
    out = capsys.readouterr().out
    assert out.startswith(function.__name__ + "(")
    for text in contains:
        assert text in out
    return out


EXPORTS = [(mm.writeMP4, "mp4"), (mm.writeAVI, "avi"), (mm.writeQuicktime, "mov")]


@pytest.mark.parametrize("export, fmt", EXPORTS, ids=lambda x: getattr(x, "__name__", x))
def test_each_format_round_trips(cwd_tmp, export, fmt):
    export(_movie(8), "anim." + fmt)
    path = cwd_tmp / ("anim." + fmt)
    assert path.stat().st_size > 0
    assert _container(str(path)) == fmt
    meta, frames = _readBack(str(path))
    assert len(frames) == 8
    assert meta["fps"] == pytest.approx(16)
    assert frames[0].shape == (48, 64, 3)
    # Frames are written in order: the red level rises frame by frame.
    reds = [frame[..., 0].mean() for frame in frames]
    assert reds == sorted(reds)


def test_custom_frame_rate(cwd_tmp):
    mm.writeAVI(_movie(), "anim.avi", 30)
    meta, _ = _readBack(str(cwd_tmp / "anim.avi"))
    assert meta["fps"] == pytest.approx(30)


def test_existing_file_is_overwritten(cwd_tmp):
    mm.writeMP4(_movie(8), "anim.mp4")
    mm.writeMP4(_movie(3), "anim.mp4")
    assert len(_readBack(str(cwd_tmp / "anim.mp4"))[1]) == 3


def test_relative_path_uses_media_folder(tmp_media, cwd_tmp):
    mm.writeMP4(_movie(2), "anim.mp4")
    assert (tmp_media / "anim.mp4").is_file()
    assert not (cwd_tmp / "anim.mp4").exists()


# extensions ---------------------------------------------------------------

def test_extension_added_when_missing(cwd_tmp):
    mm.writeAVI(_movie(2), "anim")
    assert os.listdir(cwd_tmp) == ["anim.avi"]


def test_extension_added_when_different(cwd_tmp):
    mm.writeQuicktime(_movie(2), "anim.mp4")
    assert os.listdir(cwd_tmp) == ["anim.mp4.mov"]
    assert _container(str(cwd_tmp / "anim.mp4.mov")) == "mov"


def test_upper_case_extension_kept(cwd_tmp):
    mm.writeMP4(_movie(2), "anim.MP4")
    assert os.listdir(cwd_tmp) == ["anim.MP4"]


@pytest.mark.parametrize("name, fmt", [("anim.mov", "mov"), ("anim.AVI", "avi"),
                                       ("anim.mp4", "mp4")])
def test_write_movie_by_extension(cwd_tmp, name, fmt):
    mm.writeMovie(_movie(2), name)
    assert os.listdir(cwd_tmp) == [name]
    assert _container(str(cwd_tmp / name)) == fmt


def test_write_movie_default_format(cwd_tmp):
    mm.writeMovie(_movie(2), "anim")
    assert os.listdir(cwd_tmp) == ["anim.mp4"]
    assert _container(str(cwd_tmp / "anim.mp4")) == "mp4"


def test_write_movie_changed_default_format(cwd_tmp):
    mm.setMovieFormat("avi")
    mm.writeMovie(_movie(2), "anim")
    assert os.listdir(cwd_tmp) == ["anim.avi"]
    assert _container(str(cwd_tmp / "anim.avi")) == "avi"


def test_write_movie_unsupported_extension(cwd_tmp, capsys):
    _expectError(capsys, mm.writeMovie, _movie(2), "anim.gif",
                 contains=("mp4", "avi", "mov"))
    assert os.listdir(cwd_tmp) == []


# validation ---------------------------------------------------------------

@pytest.mark.parametrize("export, fmt", EXPORTS + [(mm.writeMovie, "mp4")],
                         ids=lambda x: getattr(x, "__name__", x))
@pytest.mark.parametrize("args", [("anim",), ("EMPTY",), ("MOVIE", 0), ("MOVIE", -2),
                                  ("MOVIE", "fast"), ("MOVIE", True)])
def test_invalid_input_creates_no_file(cwd_tmp, capsys, export, fmt, args):
    stand = {"EMPTY": mm.makeMovie(), "MOVIE": _movie(2)}
    args = [stand.get(a, a) if isinstance(a, str) else a for a in args]
    _expectError(capsys, export, args[0], "anim." + fmt, *args[1:])
    assert os.listdir(cwd_tmp) == []


def test_mixed_sizes_name_first_different_frame(cwd_tmp, capsys):
    sizes = [(320, 240)] * 11 + [(640, 480)] + [(320, 240)] * 3
    out = _expectError(capsys, mm.writeMP4, _movie(15, sizes=sizes), "anim.mp4")
    assert "Frame 12 is 640x480 but frame 1 is 320x240" in out
    assert os.listdir(cwd_tmp) == []


def test_mixed_colour_modes(tmp_path, cwd_tmp, frames_factory):
    paths = (frames_factory(tmp_path, 1, mode="RGBA", pattern="a{:02d}")
             + frames_factory(tmp_path, 1, mode="RGB", ext="jpg", pattern="b{:02d}")
             + frames_factory(tmp_path, 1, mode="L", pattern="c{:02d}"))
    movie = mm.makeMovie()
    for path in paths:
        mm.addFrameToMovie(path, movie)
    mm.writeMP4(movie, "anim.mp4")
    meta, frames = _readBack(str(cwd_tmp / "anim.mp4"))
    assert len(frames) == 3


def test_odd_size_padded_to_even(cwd_tmp):
    mm.writeMP4(_movie(3, size=(101, 79)), "anim.mp4")
    meta, frames = _readBack(str(cwd_tmp / "anim.mp4"))
    assert meta["size"] == (102, 80)
    assert frames[0].shape == (80, 102, 3)


def test_missing_output_folder(cwd_tmp, capsys):
    folder = os.path.join(str(cwd_tmp), "nofolder")
    _expectError(capsys, mm.writeMP4, _movie(2), "nofolder/anim.mp4", contains=(folder,))
    assert os.listdir(cwd_tmp) == []


def test_partial_file_removed_on_encoder_failure(cwd_tmp, monkeypatch):
    realLoad = mm._loadImage
    loaded = []

    def failOnThird(entry):
        loaded.append(entry)
        if len(loaded) == 3:
            raise RuntimeError("encoder failed")
        return realLoad(entry)
    monkeypatch.setattr(mm, "_loadImage", failOnThird)
    with pytest.raises(RuntimeError):
        mm.writeMP4(_movie(5), "anim.mp4")
    assert os.listdir(cwd_tmp) == []
