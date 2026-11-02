import os

import pytest
from mediaComp import getMediaFolder

import mediaCompMovie as mm


def test_error_convention_prints_signature_and_raises(capsys):
    with pytest.raises(ValueError):
        mm._fail("someFunction(a, b)", "Something is wrong")
    assert capsys.readouterr().out == "someFunction(a, b): Something is wrong\n"


def test_absolute_path_is_unchanged(tmp_path):
    path = str(tmp_path / "frames" / "frame0001.png")
    assert mm._resolve(path) == path


def test_relative_path_without_media_folder_uses_cwd(cwd_tmp):
    assert getMediaFolder() == ""
    expected = os.path.join(str(cwd_tmp), "frames", "frame0001.png")
    assert mm._resolve(os.path.join("frames", "frame0001.png")) == expected


def test_relative_path_with_media_folder(tmp_media, cwd_tmp):
    assert mm._resolve("frames") == os.path.join(str(tmp_media), "frames")
