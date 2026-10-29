import mediaComp

import mediaCompMovie as mm

EXPECTED = {
    "makeMovie", "makeMovieFromInitialFile", "addFrameToMovie", "writeFrame",
    "writeFramesToDirectory", "playMovie", "setPlayBlocking", "getPlayBlocking",
    "writeMovie", "writeMP4", "writeAVI", "writeQuicktime",
    "setMovieFormat", "getMovieFormat",
}


def test_star_import_exposes_exactly_the_student_functions():
    namespace = {}
    exec("from mediaCompMovie import *", namespace)
    del namespace["__builtins__"]
    assert set(namespace) == EXPECTED
    assert len(mm.__all__) == len(EXPECTED)


def test_star_import_overrides_no_mediacomp_names():
    namespace = {}
    exec("from mediaComp import *", namespace)
    before = dict(namespace)
    exec("from mediaCompMovie import *", namespace)
    assert not set(mm.__all__) & set(mediaComp.__all__)
    for name, value in before.items():
        assert namespace[name] is value, name


def test_every_public_function_has_a_docstring():
    for name in mm.__all__:
        doc = getattr(mm, name).__doc__
        assert doc and doc.strip(), name
