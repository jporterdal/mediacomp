import os

import PIL.Image

import mediaCompMovie as mm


def test_empty_movie_description():
    movie = mm.Movie()
    assert len(movie) == 0
    assert str(movie) == "Movie, frames: 0"


def test_three_frames_len_index_and_description(tmp_path, frames_factory):
    paths = frames_factory(tmp_path, 3)
    movie = mm.Movie()
    for path in paths:
        movie.addFrame(path)
    assert len(movie) == 3
    assert movie[0] == paths[0]
    assert movie[-1] == paths[2]
    assert str(movie) == "Movie, frames: 3"


def test_order_past_frame_999():
    names = ["frame1000.png", "frame998.png", "frame999.png"]
    assert sorted(names, key=mm._frameSortKey) == [
        "frame998.png", "frame999.png", "frame1000.png"]


def test_order_with_mixed_padding():
    names = ["frame002.png", "frame0001.png"]
    assert sorted(names, key=mm._frameSortKey) == ["frame0001.png", "frame002.png"]


def test_scan_keeps_images_only_and_any_extension_case(tmp_path):
    for name, fmt in [("frame001.png", "PNG"), ("frame002.PNG", "PNG"),
                      ("frame003.JPG", "JPEG"), ("frame004.jpeg", "JPEG")]:
        PIL.Image.new("RGB", (4, 4)).save(str(tmp_path / name), format=fmt)
    (tmp_path / "notes.txt").write_text("not a frame")
    (tmp_path / "frame005.png").mkdir()
    found = [os.path.basename(p) for p in mm._scanDirectory(str(tmp_path))]
    assert found == ["frame001.png", "frame002.PNG", "frame003.JPG", "frame004.jpeg"]


def test_scan_of_missing_directory_is_empty(tmp_path):
    assert mm._scanDirectory(str(tmp_path / "missing")) == []


def test_directory_movie_counts_current_files(tmp_path, frames_factory):
    movie = mm.Movie(str(tmp_path))
    assert str(movie) == "Movie, frames: 0"
    frames_factory(tmp_path, 4)
    assert str(movie) == "Movie, frames: 4"
