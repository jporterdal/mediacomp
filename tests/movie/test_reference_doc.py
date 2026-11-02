"""The function reference source (contrib/movie/docs/movie-functions.md)
stays in step with mediaCompMovie.

MOVIE_REFDOC_SOURCE, if set, names another source file to check, so the
test itself can be tried against a broken one.
"""

import ast
import importlib.util
import inspect
import os

import pytest

import mediaCompMovie as mm

_DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(mm.__file__)), "docs")


def _loadRefdoc():
    spec = importlib.util.spec_from_file_location(
        "refdoc", os.path.join(_DOCS_DIR, "refdoc.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


refdoc = _loadRefdoc()


@pytest.fixture(scope="module")
def doc():
    return refdoc.parse(os.environ.get("MOVIE_REFDOC_SOURCE", refdoc.SOURCE))


def _entriesFor(doc, name):
    return [entry for entry in doc.entries()
            if any(sig.name == name for sig in entry.signatures)]


def _entryFor(doc, name):
    entries = _entriesFor(doc, name)
    assert len(entries) == 1, "%s is documented %d times, not once" % (name, len(entries))
    return entries[0]


@pytest.mark.parametrize("name", mm.__all__)
def test_documented_exactly_once(doc, name):
    _entryFor(doc, name)
    signatures = [sig for entry in doc.entries() for sig in entry.signatures
                  if sig.name == name]
    assert len(signatures) == 1, "%s has %d signature headings" % (name, len(signatures))


def test_only_public_functions_are_documented(doc):
    documented = {sig.name for entry in doc.entries() for sig in entry.signatures}
    extra = sorted(documented - set(mm.__all__))
    assert not extra, "documented but not in mediaCompMovie.__all__: " + ", ".join(extra)


@pytest.mark.parametrize("name", mm.__all__)
def test_signature_matches_code(doc, name):
    entry = _entryFor(doc, name)
    sig = next(sig for sig in entry.signatures if sig.name == name)
    params = list(inspect.signature(getattr(mm, name)).parameters.values())
    for param in params:
        assert param.kind == param.POSITIONAL_OR_KEYWORD, (
            "%s has a %s parameter %s, which the reference cannot show"
            % (name, param.kind.description, param.name))
    actual = [(param.name, param.default is not param.empty) for param in params]
    assert [p for p, _ in sig.params] == [p for p, _ in actual], (
        "%s: heading %s has parameters %s, the code has %s"
        % (name, sig.text, [p for p, _ in sig.params], [p for p, _ in actual]))
    assert sig.params == actual, (
        "%s: brackets in %s must mark exactly the parameters with defaults: %s"
        % (name, sig.text, [p for p, optional in actual if optional]))


@pytest.mark.parametrize("name", mm.__all__)
def test_parameter_lines_match_signature(doc, name):
    entry = _entryFor(doc, name)
    assert [param.name for param in entry.params] == entry.paramNames(), (
        "%s: parameter lines %s do not match the heading parameters %s"
        % (entry.name, [param.name for param in entry.params], entry.paramNames()))
    optional = {param for sig in entry.signatures for param, isOptional in sig.params
                if isOptional}
    for param in entry.params:
        endsOptional = param.text.rstrip().endswith("(optional)")
        assert endsOptional == (param.name in optional), (
            "%s: the %s line must %send with (optional)"
            % (entry.name, param.name, "" if param.name in optional else "not "))
    assert entry.returns, "%s: missing returns:" % entry.name


@pytest.mark.parametrize("name", mm.__all__)
def test_examples_are_python3(doc, name):
    entry = _entryFor(doc, name)
    for example in entry.examples:
        source = "\n".join(example.code.lines)
        try:
            ast.parse(source)
        except SyntaxError as error:
            pytest.fail("%s: example at source line %d is not Python 3: %s"
                        % (entry.name, example.code.line, error))


def test_other_code_blocks_are_python3(doc):
    for section in doc.sections:
        for block in section.blocks:
            if isinstance(block, refdoc.Code):
                try:
                    ast.parse("\n".join(block.lines))
                except SyntaxError as error:
                    pytest.fail("%s: code block at source line %d is not Python 3: %s"
                                % (section.title, block.line, error))


def test_entries_are_alphabetical(doc):
    for section in doc.sections:
        names = [entry.signatures[0].name for entry in section.entries]
        assert names == sorted(names, key=str.lower), (
            "%s: entries are not in alphabetical order: %s" % (section.title, names))
