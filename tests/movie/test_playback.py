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

@pytest.mark.parametrize("arg", ["frames", None, "EMPTY", "EMPTYDIR"])
def test_invalid_input_starts_nothing(tmp_path, capsys, popen_calls, player_state, arg):
    stand = {"EMPTY": mm.makeMovie(), "EMPTYDIR": mm.makeMovie(str(tmp_path))}
    with pytest.raises(ValueError):
        mm.playMovie(stand.get(arg, arg))
    assert capsys.readouterr().out.startswith("playMovie(movie[, isBlocking]): ")
    assert popen_calls == []
    assert _leftoverTempdirs(player_state) == []


@pytest.mark.parametrize("keyword", ["framesPerSec", "delay", "block"])
def test_old_keywords_are_rejected(popen_calls, player_state, keyword):
    with pytest.raises(TypeError, match=keyword):
        mm.playMovie(_movie(), **{keyword: 1})
    assert popen_calls == []
    assert _leftoverTempdirs(player_state) == []


def test_play_blocking_setters_are_gone_after_star_import():
    namespace = {}
    exec("from mediaCompMovie import *", namespace)
    for name in ("setPlayBlocking", "getPlayBlocking"):
        assert name not in namespace
        assert not hasattr(mm, name)
    assert not hasattr(mm, "DEFAULT_PLAY_BLOCKING")


# the player subprocess --------------------------------------------------

@pytest.mark.usefixtures("headless_sdl")
def test_non_blocking_player_exits_when_stdin_closes(popen_calls):
    movie = _movie(3)
    start = time.monotonic()
    mm.playMovie(movie)
    assert time.monotonic() - start < 5
    call = popen_calls[-1]
    proc = call["proc"]
    assert proc in mm._players
    assert call["args"][-2] == "--play"
    with open(call["args"][-1]) as f:
        assert json.load(f)["fps"] == 16

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
    mm.playMovie(_movie())
    mm.playMovie(_movie())
    time.sleep(1.0)
    assert len(mm._players) == 2
    assert all(call["proc"].poll() is None for call in popen_calls)


@pytest.mark.parametrize("isBlocking", [True, 1, 0.1])
@pytest.mark.usefixtures("headless_sdl")
def test_blocking_call_returns_when_player_stops(popen_calls, player_state, isBlocking):
    timer = threading.Timer(1.5, lambda: popen_calls[-1]["proc"].stdin.close())
    timer.start()
    start = time.monotonic()
    try:
        mm.playMovie(_movie(), isBlocking)
    finally:
        timer.cancel()
    assert time.monotonic() - start >= 1.4
    assert popen_calls[-1]["proc"].returncode == 0
    assert popen_calls[-1]["proc"] not in mm._players
    assert _leftoverTempdirs(player_state) == []


@pytest.mark.parametrize("isBlocking", [False, 0, None])
@pytest.mark.usefixtures("headless_sdl")
def test_false_value_does_not_block(popen_calls, isBlocking):
    start = time.monotonic()
    mm.playMovie(_movie(), isBlocking)
    assert time.monotonic() - start < 5
    assert popen_calls[-1]["proc"] in mm._players
    assert popen_calls[-1]["proc"].poll() is None


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
