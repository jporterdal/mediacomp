"""Export without imageio/imageio-ffmpeg, simulated whether or not they are installed."""

import importlib
import sys

import pytest
from mediaComp import makeEmptyPicture

import mediaCompMovie as mm

HINT = ("Movie export needs: pip install imageio imageio-ffmpeg "
        "(Thonny: Tools → Manage packages)")
EXPORTERS = [mm.writeMovie, mm.writeMP4, mm.writeAVI, mm.writeQuicktime]


@pytest.fixture
def no_export_packages(monkeypatch):
    for name in ["imageio", "imageio.v2", "imageio.v3", "imageio_ffmpeg"]:
        monkeypatch.setitem(sys.modules, name, None)


@pytest.fixture(autouse=True)
def reset_format():
    yield
    mm.DEFAULT_MOVIE_FORMAT = "mp4"


def _movie():
    movie = mm.makeMovie()
    mm.addFrameToMovie(makeEmptyPicture(16, 12), movie)
    return movie


@pytest.mark.parametrize("export", EXPORTERS, ids=lambda f: f.__name__)
def test_export_prints_hint_and_creates_nothing(no_export_packages, cwd_tmp, capsys,
                                                export):
    with pytest.raises(ValueError):
        export(_movie(), "anim")
    assert capsys.readouterr().out == HINT + "\n"
    assert list(cwd_tmp.iterdir()) == []


def test_module_imports_without_export_packages(no_export_packages, monkeypatch):
    monkeypatch.delitem(sys.modules, "mediaCompMovie")
    module = importlib.import_module("mediaCompMovie")
    namespace = {}
    exec("from mediaCompMovie import *", namespace)
    assert "writeMP4" in namespace
    assert module is not mm


@pytest.mark.parametrize("value, expected", [
    ("avi", "avi"), ("MOV", "mov"), (".mp4", "mp4"), (".AVI", "avi"),
])
def test_set_movie_format(value, expected):
    mm.setMovieFormat(value)
    assert mm.getMovieFormat() == expected


@pytest.mark.parametrize("value", ["gif", "", ".", 42, None, "mp4 "])
def test_set_movie_format_rejects_others(capsys, value):
    mm.setMovieFormat("avi")
    with pytest.raises(ValueError):
        mm.setMovieFormat(value)
    out = capsys.readouterr().out
    assert out.startswith("setMovieFormat(")
    assert "mp4" in out and "avi" in out and "mov" in out
    assert mm.getMovieFormat() == "avi"


def test_set_movie_format_after_star_import():
    namespace = {}
    exec("from mediaCompMovie import *\n"
         "setMovieFormat('avi')\n"
         "result = getMovieFormat()\n", namespace)
    assert namespace["result"] == "avi"
