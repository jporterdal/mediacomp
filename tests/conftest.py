"""Shared test setup for the movie tests.

Importing mediaComp reads and writes ~/.mediaCompConfig, so HOME and
USERPROFILE are pointed at a throwaway directory before anything imports it.
"""

import os
import sys
import tempfile

_TEST_HOME = tempfile.mkdtemp(prefix="mediaCompTestHome-")
os.environ["HOME"] = _TEST_HOME
os.environ["USERPROFILE"] = _TEST_HOME

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TESTS_DIR)
_WINDOWS_DIR = os.path.join(_TESTS_DIR, "windows")
sys.path.insert(0, os.path.join(_REPO_ROOT, "contrib", "movie"))

import subprocess

import pytest
import PIL.Image


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "windows: Windows-only test, skipped on other platforms")


def pytest_collection_modifyitems(config, items):
    skipWindows = pytest.mark.skip(reason="Windows-only test")
    for item in items:
        if str(item.path).startswith(_WINDOWS_DIR + os.sep):
            item.add_marker(pytest.mark.windows)
            if sys.platform != "win32":
                item.add_marker(skipWindows)


@pytest.fixture
def tmp_media(tmp_path):
    """A temp directory set as mediaComp's media folder, restored afterwards."""
    from mediaComp.core import utils
    media = tmp_path / "media"
    media.mkdir()
    old = utils.config.getMediaPath()
    utils.config.setMediaPath(str(media) + os.sep)
    yield media
    utils.config.setMediaPath(old)


@pytest.fixture
def cwd_tmp(tmp_path, monkeypatch):
    """chdir into a temp directory for the duration of the test."""
    work = tmp_path / "cwd"
    work.mkdir()
    monkeypatch.chdir(work)
    return work


@pytest.fixture
def frames_factory():
    """Return make(directory, count, ...) that writes distinct frame images.

    Frame i is filled with a colour derived from i, so frames can be told
    apart after a round trip. Returns the list of absolute paths written.
    """
    def make(directory, count, size=(32, 24), mode="RGB", ext="png",
             pattern="frame{:04d}", start=1):
        os.makedirs(directory, exist_ok=True)
        paths = []
        for i in range(start, start + count):
            shade = (i * 37) % 256
            color = {"RGB": (shade, 255 - shade, 128),
                     "RGBA": (shade, 255 - shade, 128, 200),
                     "L": shade}[mode]
            path = os.path.join(str(directory), pattern.format(i) + "." + ext)
            PIL.Image.new(mode, size, color).save(path)
            paths.append(os.path.abspath(path))
        return paths
    return make


@pytest.fixture
def popen_calls(monkeypatch):
    """Record every Popen call (its command, keywords and process)."""
    calls = []
    realPopen = subprocess.Popen

    def record(*args, **kwargs):
        proc = realPopen(*args, **kwargs)
        calls.append({"args": args[0], "kwargs": kwargs, "proc": proc})
        return proc
    monkeypatch.setattr(subprocess, "Popen", record)
    return calls


@pytest.fixture
def headless_sdl(monkeypatch):
    """Make pygame (in this process and in subprocesses) use no display."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
