"""playMovie: validation, and the player subprocess with no display."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time

import pytest
from mediaComp import makeColor, makeEmptyPicture

import mediaCompMovie as mm


@pytest.fixture(autouse=True)
def player_state(tmp_path, monkeypatch):
    """Send playback temp dirs to tmp_path and stop leftover players afterwards."""
    tempRoot = tmp_path / "tmp"
    tempRoot.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(tempRoot))
    yield tempRoot
    for proc in list(mm._players):
        mm._stopPlayer(proc)
    mm._players.clear()
    mm.DEFAULT_PLAY_BLOCKING = True


def _movie(count=3):
    movie = mm.makeMovie()
    for num in range(count):
        mm.addFrameToMovie(makeEmptyPicture(16, 12, makeColor(num * 40, 0, 0)), movie)
    return movie


def _tempdirOf(call):
    return os.path.dirname(call["args"][-1])


def _leftoverTempdirs(tempRoot):
    return [name for name in os.listdir(tempRoot) if name.startswith("mediaCompMovie-")]


# validation -------------------------------------------------------------

@pytest.mark.parametrize("args, kwargs", [
    (("frames",), {}),
    ((None,), {}),
    (("EMPTY",), {}),
    (("EMPTYDIR",), {}),
    (("MOVIE", 0.1), {"framesPerSec": 30}),
    (("MOVIE", 0), {}),
    (("MOVIE", -1), {}),
    (("MOVIE", "fast"), {}),
    (("MOVIE", True), {}),
    (("MOVIE", float("inf")), {}),
    (("MOVIE",), {"framesPerSec": -5}),
    (("MOVIE",), {"framesPerSec": 0}),
    (("MOVIE",), {"block": "yes"}),
])
def test_invalid_input_starts_nothing(tmp_path, capsys, popen_calls, player_state,
                                      args, kwargs):
    stand = {"EMPTY": mm.makeMovie(), "MOVIE": _movie(),
             "EMPTYDIR": mm.makeMovie(str(tmp_path))}
    args = tuple(stand.get(a, a) if isinstance(a, str) else a for a in args)
    with pytest.raises(ValueError):
        mm.playMovie(*args, **kwargs)
    assert capsys.readouterr().out.startswith("playMovie(")
    assert popen_calls == []
    assert _leftoverTempdirs(player_state) == []


# the player subprocess --------------------------------------------------

@pytest.mark.usefixtures("headless_sdl")
def test_non_blocking_player_exits_when_stdin_closes(popen_calls):
    movie = _movie(3)
    start = time.monotonic()
    mm.playMovie(movie, block=False)
    assert time.monotonic() - start < 5
    call = popen_calls[-1]
    proc = call["proc"]
    assert proc in mm._players
    assert call["args"][-2] == "--play"

    # The window plays the frames the movie had when playMovie was called.
    mm.addFrameToMovie(makeEmptyPicture(16, 12), movie)
    pngs = [n for n in os.listdir(_tempdirOf(call)) if n.endswith(".png")]
    assert len(pngs) == 3

    time.sleep(1.5)
    assert proc.poll() is None, "player should keep running while stdin is open"
    proc.stdin.close()
    assert proc.wait(timeout=15) == 0
    assert not os.path.exists(_tempdirOf(call))


@pytest.mark.usefixtures("headless_sdl")
def test_two_non_blocking_players_at_once(popen_calls):
    mm.playMovie(_movie(), block=False)
    mm.playMovie(_movie(), block=False)
    time.sleep(1.0)
    assert len(mm._players) == 2
    assert all(call["proc"].poll() is None for call in popen_calls)


@pytest.mark.usefixtures("headless_sdl")
def test_blocking_call_returns_when_player_stops(popen_calls, player_state):
    timer = threading.Timer(1.5, lambda: popen_calls[-1]["proc"].stdin.close())
    timer.start()
    start = time.monotonic()
    try:
        mm.playMovie(_movie(), 0.25)
    finally:
        timer.cancel()
    assert time.monotonic() - start >= 1.4
    assert popen_calls[-1]["proc"].returncode == 0
    assert popen_calls[-1]["proc"] not in mm._players
    assert _leftoverTempdirs(player_state) == []


@pytest.mark.skipif(sys.platform == "win32", reason="uses SIGTERM, which SDL turns into a quit")
@pytest.mark.usefixtures("headless_sdl")
def test_player_closed_while_parent_alive_exits_cleanly(tmp_path):
    # Closing the window (or Escape) while stdin is still open must not leave
    # the stdin watcher holding a lock that aborts interpreter shutdown.
    tempdir = tmp_path / "mediaCompMovie-x"
    tempdir.mkdir()
    frame = str(tempdir / "0001.png")
    makeEmptyPicture(16, 12).getImage().save(frame)
    manifest = str(tempdir / "manifest.json")
    with open(manifest, "w") as f:
        json.dump({"frames": [frame], "fps": 16, "tempdir": str(tempdir)}, f)
    proc = subprocess.Popen([sys.executable, mm.__file__, "--play", manifest],
                            stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        time.sleep(1.5)
        assert proc.poll() is None
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=15)       # not communicate(): that would close stdin
        err = proc.stderr.read()
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.stdin.close()
        proc.stderr.close()
    assert err.decode() == ""
    assert proc.returncode == 0
    assert not tempdir.exists()


# blocking default -------------------------------------------------------

def test_set_and_get_play_blocking_after_star_import():
    namespace = {}
    exec("from mediaCompMovie import *\n"
         "before = getPlayBlocking()\n"
         "setPlayBlocking(False)\n"
         "after = getPlayBlocking()\n", namespace)
    assert namespace["before"] is True
    assert namespace["after"] is False
    assert mm.DEFAULT_PLAY_BLOCKING is False


@pytest.mark.parametrize("value", [1, 0, "yes", None])
def test_set_play_blocking_rejects_non_bool(capsys, value):
    with pytest.raises(ValueError):
        mm.setPlayBlocking(value)
    assert capsys.readouterr().out.startswith("setPlayBlocking(")
    assert mm.getPlayBlocking() is True


@pytest.mark.usefixtures("headless_sdl")
def test_module_default_non_blocking(popen_calls):
    mm.setPlayBlocking(False)
    start = time.monotonic()
    mm.playMovie(_movie())
    assert time.monotonic() - start < 5
    assert popen_calls[-1]["proc"] in mm._players
    assert popen_calls[-1]["proc"].poll() is None


@pytest.mark.usefixtures("headless_sdl")
def test_block_keyword_overrides_default(popen_calls):
    mm.setPlayBlocking(False)
    timer = threading.Timer(1.5, lambda: popen_calls[-1]["proc"].stdin.close())
    timer.start()
    start = time.monotonic()
    try:
        mm.playMovie(_movie(), block=True)
    finally:
        timer.cancel()
    assert time.monotonic() - start >= 1.4
    assert popen_calls[-1]["proc"].returncode == 0
