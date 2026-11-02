"""Windows path handling. Skipped on other platforms (see conftest.py)."""

import os

import pytest
from mediaComp import makeEmptyPicture
from mediaComp.core import utils

import mediaCompMovie as mm


@pytest.fixture
def media_path():
    """Return set(path) that sets the media folder as stored, restored afterwards."""
    old = utils.config.getMediaPath()
    yield utils.config.setMediaPath
    utils.config.setMediaPath(old)


def test_drive_letter_path_is_unchanged():
    assert mm._resolve(r"C:\media\frames") == r"C:\media\frames"


def test_media_folder_spec_example(media_path):
    media_path("C:\\media\\")
    assert mm._resolve("frames") == r"C:\media\frames"


def test_backslash_relative_path_without_media_folder(cwd_tmp):
    assert utils.config.getMediaPath() == ""
    expected = os.path.join(str(cwd_tmp), "frames", "frame0001.png")
    assert mm._resolve(r"frames\frame0001.png") == expected
    assert mm._resolve("frames/frame0001.png") == expected


@pytest.mark.parametrize("trailing", ["", "\\"], ids=["no-separator", "separator"])
def test_media_folder_with_and_without_trailing_separator(tmp_path, media_path, trailing):
    media_path(str(tmp_path) + trailing)
    assert mm._resolve("frames") == os.path.join(str(tmp_path), "frames")


def test_spaces_in_paths(tmp_path, media_path):
    media = tmp_path / "my media"
    media.mkdir()
    media_path(str(media) + "\\")
    mm.writeFrame(1, "my frames", makeEmptyPicture(8, 8))
    mm.writeFrame(2, "my frames", makeEmptyPicture(8, 8))
    assert (media / "my frames" / "frame0002.png").is_file()
    movie = mm.makeMovieFromInitialFile(r"my frames\frame0001.png")
    assert len(movie) == 2
    assert len(mm.makeMovie("my frames")) == 2
