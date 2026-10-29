"""Windows player process handling. Skipped on other platforms (see conftest.py)."""

import ctypes
import os
import subprocess
import sys
import textwrap
import time

import pytest
from mediaComp import makeEmptyPicture

import mediaCompMovie as mm

pytestmark = pytest.mark.usefixtures("headless_sdl")


@pytest.fixture(autouse=True)
def stop_players():
    yield
    for proc in list(mm._players):
        mm._stopPlayer(proc)
    mm._players.clear()


def _movie():
    movie = mm.makeMovie()
    mm.addFrameToMovie(makeEmptyPicture(16, 12), movie)
    return movie


def _alive(pid):
    # os.kill(pid, 0) would terminate the process on Windows, so ask the OS.
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    code = ctypes.c_ulong()
    kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    kernel32.CloseHandle(handle)
    return code.value == 259  # STILL_ACTIVE


def _waitUntilGone(pid, timeout=15):
    deadline = time.monotonic() + timeout
    while _alive(pid) and time.monotonic() < deadline:
        time.sleep(0.2)
    return not _alive(pid)


def test_create_no_window_is_passed(popen_calls):
    mm.playMovie(_movie(), block=False)
    flags = popen_calls[-1]["kwargs"].get("creationflags", 0)
    assert flags & subprocess.CREATE_NO_WINDOW


def test_player_exits_when_parent_closes_stdin(popen_calls):
    mm.playMovie(_movie(), block=False)
    proc = popen_calls[-1]["proc"]
    time.sleep(1.5)
    assert proc.poll() is None
    proc.stdin.close()
    assert proc.wait(timeout=15) == 0


def test_player_exits_when_parent_is_killed(tmp_path):
    # Thonny's Stop/Restart terminates the backend process outright.
    script = tmp_path / "parent.py"
    script.write_text(textwrap.dedent("""
        import sys, time
        sys.path.insert(0, %r)
        from mediaComp import makeEmptyPicture
        import mediaCompMovie as mm
        movie = mm.makeMovie()
        mm.addFrameToMovie(makeEmptyPicture(16, 12), movie)
        mm.playMovie(movie, block=False)
        print(mm._players[-1].pid, flush=True)
        time.sleep(120)
    """ % os.path.dirname(os.path.abspath(mm.__file__))))
    parent = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.PIPE, text=True)
    try:
        pid = int(parent.stdout.readline())
        time.sleep(1.5)
        assert _alive(pid)
        parent.kill()
        parent.wait()
        assert _waitUntilGone(pid), "player outlived the process that started it"
    finally:
        if parent.poll() is None:
            parent.kill()
        parent.stdout.close()
