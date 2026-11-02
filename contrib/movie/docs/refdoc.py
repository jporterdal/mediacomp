"""Read movie-functions.md, the source of the movie function reference.

The source is a small, strict subset of Markdown, so that it reads well on
GitHub and can be checked against the code. build.py turns the document
model into Movie Functions.docx, and tests/movie/test_reference_doc.py
compares it with mediaCompMovie.

The format:

    ---                             front matter, "key: value" lines
    title: ...                      (title, subtitle, basedOn, date, footer)
    ---

    # Heading                       a section (Heading 1)
    Paragraph text, which may run   free paragraphs; *italic* and `code`
    over several lines.             are the only inline markup
    - a bullet                      bullets; indent continuation lines
    ## Heading / ### Heading        sub-headings (outside function sections)
    ```python                       a code block
    ```

A section whose heading ends in "Functions" is a function section. Its text
up to the first "##" heading is the preamble; after that, every "##" heading
is a function signature, and consecutive "##" lines share one entry. An entry
is, in this order:

    ## name(a[, b])                 one or more signature headings
    Description paragraphs.
                                    (a blank line)
    a: what a is                    the parameter block: one "name: text"
    b: what b is (optional)         line per parameter, then "returns:"
    returns: what it returns
                                    (a blank line)
    ```python                       one or more examples, each followed
    example code                    by at least one explanation paragraph
    ```
    What the example does.

Run as a script, it parses the source and prints a summary, or the first
error.
"""

import os
import re
import sys
from dataclasses import dataclass, field

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movie-functions.md")

FRONT_MATTER_KEYS = ("title", "subtitle", "basedOn", "date", "footer")
PLACEHOLDER = "TODO"

_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
_PARAM_LINE = re.compile(r"(" + _IDENTIFIER + r"):\s+(\S.*)")
_SIGNATURE = re.compile(r"(" + _IDENTIFIER + r")\((.*)\)")


class RefDocError(Exception):
    """The source does not follow the format. The message names the place."""


# ---------------------------------------------------------------------------
# Document model
# ---------------------------------------------------------------------------

# Inline text is a list of runs: (text, kind), kind None, "italic" or "code".

@dataclass
class Paragraph:
    runs: list


@dataclass
class Bullet:
    runs: list


@dataclass
class Heading:
    level: int
    runs: list


@dataclass
class Code:
    lines: list
    line: int = 0


@dataclass
class Signature:
    text: str
    name: str
    params: list            # [(name, optional)]


@dataclass
class Param:
    name: str
    runs: list

    @property
    def text(self):
        return plainText(self.runs)


@dataclass
class Example:
    code: Code
    explanation: list       # [Paragraph]


@dataclass
class Entry:
    signatures: list        # [Signature]
    description: list       # [Paragraph]
    params: list            # [Param], without returns
    returns: list           # runs
    examples: list          # [Example]
    line: int = 0

    @property
    def name(self):
        return " / ".join(sig.name for sig in self.signatures)

    def paramNames(self):
        """The parameters of all its signatures, in order of first use."""
        names = []
        for sig in self.signatures:
            for name, _ in sig.params:
                if name not in names:
                    names.append(name)
        return names


@dataclass
class Section:
    title: str
    isFunctions: bool
    blocks: list = field(default_factory=list)   # preamble or free content
    entries: list = field(default_factory=list)  # [Entry]
    line: int = 0


@dataclass
class Document:
    meta: dict
    sections: list

    def entries(self):
        return [entry for section in self.sections for entry in section.entries]


def plainText(runs):
    return "".join(text for text, _ in runs)


# ---------------------------------------------------------------------------
# Inline markup and signatures
# ---------------------------------------------------------------------------

def parseInline(text, where):
    """Split text into runs. Only `code` and *italic* are recognised."""
    runs = []
    for i, part in enumerate(text.split("`")):
        if i % 2:
            runs.append((part, "code"))
            continue
        for j, piece in enumerate(part.split("*")):
            if piece:
                runs.append((piece, "italic" if j % 2 else None))
        if part.count("*") % 2:
            raise RefDocError(where + ": unmatched * in: " + text)
    if text.count("`") % 2:
        raise RefDocError(where + ": unmatched ` in: " + text)
    return runs


def parseSignature(text, where="signature"):
    """Parse "name(a[, b[, c]])" into a Signature.

    A parameter is optional if it is inside square brackets, so both
    f(a[, b[, c]]) and f(a[, b][, c]) mark b and c optional.
    """
    match = _SIGNATURE.fullmatch(text.strip())
    if not match:
        raise RefDocError(where + ": not a signature of the form name(...): " + text)
    name, inside = match.groups()
    params = []
    depth = 0
    for token in re.findall(r"\[|\]|,|[^\[\],\s]+", inside):
        if token == "[":
            depth += 1
        elif token == "]":
            depth -= 1
            if depth < 0:
                raise RefDocError(where + ": unbalanced ] in " + text)
        elif token == ",":
            continue
        elif re.fullmatch(_IDENTIFIER, token):
            params.append((token, depth > 0))
        else:
            raise RefDocError(where + ": %r is not a plain parameter name in %s "
                              "(no defaults, keywords or *args)" % (token, text))
    if depth:
        raise RefDocError(where + ": unbalanced [ in " + text)
    names = [param for param, _ in params]
    if len(set(names)) != len(names):
        raise RefDocError(where + ": a parameter is repeated in " + text)
    return Signature(text.strip(), name, params)


# ---------------------------------------------------------------------------
# Block reader
# ---------------------------------------------------------------------------

def _readFrontMatter(lines):
    """Return (meta, index of the first line after it)."""
    if not lines or lines[0].strip() != "---":
        raise RefDocError("line 1: the source must start with --- front matter")
    meta = {}
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if line == "---":
            missing = [key for key in FRONT_MATTER_KEYS if not meta.get(key)]
            if missing:
                raise RefDocError("front matter: missing " + ", ".join(missing))
            return meta, i + 1
        if not line:
            continue
        key, sep, value = line.partition(":")
        if not sep or key.strip() not in FRONT_MATTER_KEYS:
            raise RefDocError("line %d: front matter lines are one of %s, then a colon"
                              % (i + 1, ", ".join(FRONT_MATTER_KEYS)))
        meta[key.strip()] = value.strip()
    raise RefDocError("front matter: no closing ---")


def _readBlocks(lines, start):
    """Group the body into raw blocks: (kind, line number, content).

    kinds: "h1"/"h2"/"h3" (text), "code" (lines), "para" (lines),
    "bullets" (list of texts).
    """
    blocks = []
    i = start
    while i < len(lines):
        line = lines[i]
        num = i + 1
        stripped = line.strip()
        if not stripped:
            i += 1
        elif stripped.startswith("```"):
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != "```":
                body.append(lines[i].rstrip())
                i += 1
            if i == len(lines):
                raise RefDocError("line %d: code block is never closed" % num)
            blocks.append(("code", num, body))
            i += 1
        elif re.match(r"#{1,3} ", line):
            level = len(line.split(" ", 1)[0])
            blocks.append(("h%d" % level, num, line[level:].strip()))
            i += 1
        elif line.startswith("- "):
            items = []
            while i < len(lines) and (lines[i].startswith("- ") or
                                      (items and lines[i].startswith("  ") and lines[i].strip())):
                if lines[i].startswith("- "):
                    items.append(lines[i][2:].strip())
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            blocks.append(("bullets", num, items))
        elif line.startswith("#"):
            raise RefDocError("line %d: only #, ## and ### headings are allowed" % num)
        else:
            body = []
            while (i < len(lines) and lines[i].strip()
                   and not lines[i].startswith(("#", "- ", "```"))):
                body.append(lines[i].strip())
                i += 1
            blocks.append(("para", num, body))
    return blocks


def _isParamBlock(body):
    return (all(_PARAM_LINE.fullmatch(line) for line in body)
            and body[-1].startswith("returns:"))


def _freeBlock(kind, num, content):
    where = "line %d" % num
    if kind == "para":
        return [Paragraph(parseInline(" ".join(content), where))]
    if kind == "bullets":
        return [Bullet(parseInline(item, where)) for item in content]
    if kind == "code":
        return [Code(content, num)]
    level = int(kind[1])
    return [Heading(level, parseInline(content, where))]


def _buildEntry(group):
    """Turn the raw blocks of one entry (headings first) into an Entry."""
    num = group[0][1]
    signatures = []
    pos = 0
    while pos < len(group) and group[pos][0] == "h2":
        signatures.append(parseSignature(group[pos][2], "line %d" % group[pos][1]))
        pos += 1
    entry = Entry(signatures, [], [], None, [], num)
    where = "line %d, entry %s" % (num, entry.name)

    while pos < len(group) and group[pos][0] == "para" and not _isParamBlock(group[pos][2]):
        entry.description.append(Paragraph(parseInline(" ".join(group[pos][2]), where)))
        pos += 1
    if not entry.description:
        raise RefDocError(where + ": missing the description")
    if pos == len(group) or group[pos][0] != "para":
        raise RefDocError(where + ": missing the parameter block ending in a returns: line")
    for line in group[pos][2]:
        name, text = _PARAM_LINE.fullmatch(line).groups()
        if name == "returns":
            entry.returns = parseInline(text, where)
        else:
            entry.params.append(Param(name, parseInline(text, where)))
    pos += 1

    while pos < len(group):
        kind, line, content = group[pos]
        if kind != "code":
            raise RefDocError("line %d, entry %s: expected an example code block, found %s"
                              % (line, entry.name, "text" if kind == "para" else kind))
        example = Example(Code(content, line), [])
        pos += 1
        while pos < len(group) and group[pos][0] == "para":
            example.explanation.append(
                Paragraph(parseInline(" ".join(group[pos][2]), where)))
            pos += 1
        if not example.explanation:
            raise RefDocError("line %d, entry %s: the example needs a sentence explaining it"
                              % (line, entry.name))
        entry.examples.append(example)
    if not entry.examples:
        raise RefDocError(where + ": missing an example")
    return entry


def parseText(text):
    """Parse the source text into a Document, or raise RefDocError."""
    lines = text.splitlines()
    meta, start = _readFrontMatter(lines)
    sections = []
    section = None
    group = None        # raw blocks of the entry being read
    for kind, num, content in _readBlocks(lines, start):
        if kind == "h1":
            if group:
                section.entries.append(_buildEntry(group))
            group = None
            section = Section(content, content.endswith("Functions"), line=num)
            sections.append(section)
            continue
        if section is None:
            raise RefDocError("line %d: text before the first # heading" % num)
        if section.isFunctions:
            if kind == "h3":
                raise RefDocError("line %d: ### headings are not allowed in a "
                                  "function section" % num)
            if kind == "h2":
                if group and group[-1][0] != "h2":
                    section.entries.append(_buildEntry(group))
                    group = None
                group = (group or []) + [(kind, num, content)]
                continue
            if group:
                group.append((kind, num, content))
                continue
        section.blocks.extend(_freeBlock(kind, num, content))
    if group:
        section.entries.append(_buildEntry(group))
    return Document(meta, sections)


def parse(path=SOURCE):
    with open(path, encoding="utf-8") as f:
        return parseText(f.read())


if __name__ == "__main__":
    try:
        doc = parse(sys.argv[1] if len(sys.argv) > 1 else SOURCE)
    except RefDocError as error:
        print("error:", error)
        sys.exit(1)
    for section in doc.sections:
        print(section.title)
        for entry in section.entries:
            print("   ", ", ".join(sig.text for sig in entry.signatures))
