"""In-process tests of the player loop (section C) with no display."""

import json
import os

import PIL.Image
import pygame
import pytest

import mediaCompMovie as mm

pytestmark = pytest.mark.usefixtures("headless_sdl")


@pytest.fixture
def manifest(tmp_path):
    """Return make(sizes) that writes one solid frame per size and a manifest."""
    def make(sizes, fps=1000):
        tempdir = tmp_path / "mediaCompMovie-test"
        tempdir.mkdir()
        paths = []
        for num, size in enumerate(sizes, 1):
            path = str(tempdir / ("%04d.png" % num))
            PIL.Image.new("RGB", size, (255, 0, 0)).save(path)
            paths.append(path)
        path = str(tempdir / "manifest.json")
        with open(path, "w") as f:
            json.dump({"frames": paths, "fps": fps, "tempdir": str(tempdir)}, f)
        return path
    return make


def _keys(script):
    """onTick hook that posts the key events script[tick] at that tick."""
    def onTick(tick):
        for key in script.get(tick, []):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    return onTick


def test_frames_advance_in_order_and_wrap(manifest):
    titles = mm._runPlayer(manifest([(8, 8)] * 3), maxFrames=7)
    assert titles == ["Movie: frame %d of 3" % n for n in [1, 2, 3, 1, 2, 3, 1]]


def test_title_is_set_on_window(manifest):
    seen = []
    mm._runPlayer(manifest([(8, 8)] * 20), maxFrames=4,
                  onTick=lambda tick: seen.append(pygame.display.get_caption()[0]))
    assert seen[3] == "Movie: frame 3 of 20"


def test_pause_and_step_right(manifest):
    titles = mm._runPlayer(manifest([(8, 8)] * 5), maxFrames=4,
                           onTick=_keys({0: [pygame.K_SPACE], 1: [pygame.K_RIGHT]}))
    assert titles == ["Movie: frame 1 of 5 (paused)", "Movie: frame 2 of 5 (paused)",
                      "Movie: frame 2 of 5 (paused)", "Movie: frame 2 of 5 (paused)"]


def test_unpause_resumes(manifest):
    titles = mm._runPlayer(manifest([(8, 8)] * 5), maxFrames=4,
                           onTick=_keys({0: [pygame.K_SPACE], 2: [pygame.K_SPACE]}))
    assert titles == ["Movie: frame 1 of 5 (paused)", "Movie: frame 1 of 5 (paused)",
                      "Movie: frame 1 of 5", "Movie: frame 2 of 5"]


def test_arrows_ignored_while_playing(manifest):
    titles = mm._runPlayer(manifest([(8, 8)] * 5), maxFrames=3,
                           onTick=_keys({1: [pygame.K_LEFT]}))
    assert titles == ["Movie: frame %d of 5" % n for n in [1, 2, 3]]


def test_left_from_first_frame_wraps_to_last(manifest):
    titles = mm._runPlayer(manifest([(8, 8)] * 5), maxFrames=2,
                           onTick=_keys({0: [pygame.K_SPACE], 1: [pygame.K_LEFT]}))
    assert titles[-1] == "Movie: frame 5 of 5 (paused)"


def test_escape_exits(manifest):
    titles = mm._runPlayer(manifest([(8, 8)] * 3), maxFrames=100,
                           onTick=_keys({2: [pygame.K_ESCAPE]}))
    assert len(titles) == 2


def test_close_button_exits(manifest):
    def onTick(tick):
        if tick == 1:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
    assert len(mm._runPlayer(manifest([(8, 8)] * 3), maxFrames=100, onTick=onTick)) == 1


def test_window_fits_largest_frame_and_frames_are_unscaled(manifest):
    seen = {}

    def onTick(tick):
        if tick == 1:
            screen = pygame.display.get_surface()
            seen["size"] = screen.get_size()
            seen["corner"] = tuple(screen.get_at((10, 10)))[:3]
            seen["inside"] = tuple(screen.get_at((51, 26)))[:3]
    mm._runPlayer(manifest([(200, 100), (300, 150)]), maxFrames=2, onTick=onTick)
    assert seen["size"] == (300, 150)
    assert seen["corner"] == (0, 0, 0)          # frame 1 is centred, not scaled
    assert seen["inside"] == (255, 0, 0)


def test_tempdir_removed_after_exit(manifest):
    path = manifest([(8, 8)] * 2)
    mm._runPlayer(path, maxFrames=3)
    assert not os.path.exists(os.path.dirname(path))
