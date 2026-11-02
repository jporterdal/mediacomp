"""Build Movie Functions.docx and Movie Functions.pdf from movie-functions.md.

The .docx starts from upstream's Documentation/Media Functions.docx, with its
body cleared, so it has upstream's styles, page setup and "Page N" header.
The PDF is made from the .docx by LibreOffice (docx2pdf.py).

Development tools, installed once in WSL/Debian:

    sudo apt install libreoffice-writer-nogui python3-uno \\
                     fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea
    venv/bin/pip install -r contrib/movie/requirements-dev.txt

Liberation Sans and Mono have the same metrics as Arial and Courier New, so
the layout matches without the Microsoft fonts. For the exact fonts, enable
apt's contrib component and install ttf-mscorefonts-installer, or open the
.docx in Word and save it as PDF.

Run from anywhere:

    venv/bin/python contrib/movie/docs/build.py [--no-pdf]
"""

import argparse
import copy
import datetime
import os
import shutil
import subprocess
import sys

import refdoc

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
MOVIE_DIR = os.path.dirname(DOCS_DIR)
REPO_ROOT = os.path.dirname(os.path.dirname(MOVIE_DIR))
TEMPLATE = os.path.join(REPO_ROOT, "Documentation", "Media Functions.docx")
DOCX = os.path.join(MOVIE_DIR, "Movie Functions.docx")
PDF = os.path.join(MOVIE_DIR, "Movie Functions.pdf")

REQUIRED_STYLES = ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3",
                   "List Paragraph", "Program code", "Program code Char", "Footer")
APT_PACKAGES = ("libreoffice-writer-nogui python3-uno fonts-liberation "
                "fonts-crosextra-carlito fonts-crosextra-caladea")

_MONTHS = ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December")


def _fail(message):
    print("build.py: " + message, file=sys.stderr)
    sys.exit(1)


def _longDate(text):
    try:
        date = datetime.date.fromisoformat(text)
    except ValueError:
        _fail("front matter date must be YYYY-MM-DD, not " + text)
    return "%s %d, %d" % (_MONTHS[date.month - 1], date.day, date.year)


class Writer:
    """Writes the document model into a cleared copy of the template."""

    def __init__(self, template):
        import docx
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        self.OxmlElement = OxmlElement
        self.qn = qn
        self.doc = docx.Document(template)
        names = {style.name for style in self.doc.styles}
        missing = [name for name in REQUIRED_STYLES if name not in names]
        if missing:
            _fail("the template %s has no style named %s"
                  % (template, ", ".join(repr(name) for name in missing)))
        self.bulletNumId = self._findBulletNumbering()
        self.ruleParagraph = self._findRule()
        body = self.doc.element.body
        for child in list(body):
            if child.tag != qn("w:sectPr"):
                body.remove(child)

    def _findBulletNumbering(self):
        """The numId of the template's first bulleted List Paragraph, or None."""
        qn = self.qn
        ids = self.doc.element.body.xpath(
            './/w:p[w:pPr/w:pStyle/@w:val="ListParagraph"]/w:pPr/w:numPr/w:numId/@w:val')
        if not ids:
            return None
        numbering = self.doc.part.numbering_part.element
        for num in numbering.findall(qn("w:num")):
            if num.get(qn("w:numId")) != ids[0]:
                continue
            abstractId = num.find(qn("w:abstractNumId")).get(qn("w:val"))
            for abstract in numbering.findall(qn("w:abstractNum")):
                if abstract.get(qn("w:abstractNumId")) == abstractId:
                    fmt = abstract.find(qn("w:lvl")).find(qn("w:numFmt"))
                    if fmt is not None and fmt.get(qn("w:val")) == "bullet":
                        return ids[0]
        return None

    def _findRule(self):
        """A copy of the template's horizontal-rule paragraph, or None."""
        vmlRect = "{urn:schemas-microsoft-com:vml}rect"
        isRule = "{urn:schemas-microsoft-com:office:office}hr"
        for paragraph in self.doc.element.body.iter(self.qn("w:p")):
            if any(rect.get(isRule) == "t" for rect in paragraph.iter(vmlRect)):
                return copy.deepcopy(paragraph)
        return None

    # paragraphs -----------------------------------------------------------

    def para(self, style="Normal", runs=(), bold=False):
        paragraph = self.doc.add_paragraph(style=style)
        self.addRuns(paragraph, runs, bold)
        return paragraph

    def addRuns(self, paragraph, runs, bold=False):
        for text, kind in runs:
            run = paragraph.add_run(text)
            if bold:
                run.bold = True
            if kind == "italic":
                run.italic = True
            elif kind == "code":
                run.style = self.doc.styles["Program code Char"]

    def spacer(self):
        self.para()

    def rule(self):
        """A horizontal line between entries, as upstream has."""
        if self.ruleParagraph is not None:
            self.doc.element.body.sectPr.addprevious(copy.deepcopy(self.ruleParagraph))

    def underline(self, paragraph):
        """A bottom border, as under upstream's title lines."""
        border = self.OxmlElement("w:pBdr")
        bottom = self.OxmlElement("w:bottom")
        for name, value in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"),
                            ("w:color", "auto")):
            bottom.set(self.qn(name), value)
        border.append(bottom)
        pPr = paragraph._p.get_or_add_pPr()
        following = pPr.find(self.qn("w:rPr"))
        if following is not None:
            following.addprevious(border)
        else:
            pPr.append(border)

    def pageBreak(self):
        from docx.enum.text import WD_BREAK
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def bullet(self, runs):
        if self.bulletNumId is None:
            return self.para(runs=[("• ", None)] + list(runs))
        paragraph = self.para("List Paragraph", runs)
        numPr = self.OxmlElement("w:numPr")
        for tag, value in (("w:ilvl", "0"), ("w:numId", self.bulletNumId)):
            element = self.OxmlElement(tag)
            element.set(self.qn("w:val"), value)
            numPr.append(element)
        paragraph._p.get_or_add_pPr().append(numPr)
        return paragraph

    def code(self, lines):
        for line in lines:
            self.para("Program code", [(line, None)])

    def tableOfContents(self):
        self.para("Heading 1", [("Table of Contents", None)])
        paragraph = self.doc.add_paragraph()
        qn = self.qn
        for kind in ("begin", "instr", "separate", "text", "end"):
            run = self.OxmlElement("w:r")
            if kind == "instr":
                element = self.OxmlElement("w:instrText")
                element.set(qn("xml:space"), "preserve")
                element.text = ' TOC \\o "1-3" \\h \\z \\u '
            elif kind == "text":
                element = self.OxmlElement("w:t")
                element.text = "Update this field to show the table of contents."
            else:
                element = self.OxmlElement("w:fldChar")
                element.set(qn("w:fldCharType"), kind)
                if kind == "begin":
                    element.set(qn("w:dirty"), "true")
            run.append(element)
            paragraph._p.append(run)
        self._setUpdateFields()

    def _setUpdateFields(self):
        """Ask Word to refresh fields (the table of contents) on open."""
        qn = self.qn
        settings = self.doc.settings.element
        if settings.find(qn("w:updateFields")) is not None:
            return
        element = self.OxmlElement("w:updateFields")
        element.set(qn("w:val"), "true")
        # Keep the schema's element order: updateFields comes before these.
        for tag in ("w:hdrShapeDefaults", "w:footnotePr", "w:endnotePr", "w:compat",
                    "w:docVars", "w:rsids"):
            following = settings.find(qn(tag))
            if following is not None:
                following.addprevious(element)
                return
        settings.append(element)

    def footer(self, text):
        for section in self.doc.sections:
            element = section.footer._element
            for paragraph in list(element):
                element.remove(paragraph)
            section.footer.add_paragraph(style="Footer")
            section.footer.add_paragraph(text, style="Footer")

    # document parts ---------------------------------------------------------

    def titleBlock(self, meta):
        self.para("Title", [(meta["title"], None)], bold=True)
        self.underline(self.para("Title", [(meta["subtitle"], None)]))
        self.para(runs=[("Document based on " + meta["basedOn"], None)], bold=True)
        self.underline(self.para(runs=[(_longDate(meta["date"]), None)], bold=True))
        self.spacer()

    def blocks(self, blocks):
        previous = None
        for block in blocks:
            if previous is not None and not isinstance(previous, refdoc.Heading) \
                    and not (isinstance(previous, refdoc.Bullet)
                             and isinstance(block, refdoc.Bullet)):
                self.spacer()
            if isinstance(block, refdoc.Heading):
                self.para("Heading %d" % block.level, block.runs)
            elif isinstance(block, refdoc.Bullet):
                self.bullet(block.runs)
            elif isinstance(block, refdoc.Code):
                self.code(block.lines)
            else:
                self.para(runs=block.runs)
            previous = block
        if previous is not None:
            self.spacer()

    def entry(self, entry, first):
        if not first:
            self.rule()
        for sig in entry.signatures:
            self.para("Heading 2", [(sig.text, None)])
        for i, paragraph in enumerate(entry.description):
            if i:
                self.spacer()
            self.para(runs=paragraph.runs)
        self.spacer()
        for param in entry.params:
            self._label(param.name + ":", param.runs)
        self._label("returns:", entry.returns)
        self.spacer()
        self.para(runs=[("Examples:" if len(entry.examples) > 1 else "Example:", None)])
        for i, example in enumerate(entry.examples):
            if i:
                self.spacer()
            self.code(example.code.lines)
            for paragraph in example.explanation:
                self.spacer()
                self.para(runs=paragraph.runs)
        self.spacer()

    def _label(self, label, runs):
        """A parameter or returns: line, with the label in bold as upstream."""
        paragraph = self.para(runs=[(label, None)], bold=True)
        self.addRuns(paragraph, [(" ", None)] + list(runs))

    def document(self, doc):
        self.titleBlock(doc.meta)
        tocDone = False
        for i, section in enumerate(doc.sections):
            if section.isFunctions and not tocDone:
                self.pageBreak()
                self.tableOfContents()
                tocDone = True
            if i:
                self.pageBreak()
            self.para("Heading 1", [(section.title, None)])
            self.blocks(section.blocks)
            for num, entry in enumerate(section.entries):
                self.entry(entry, first=(num == 0 and not section.blocks))
        if not tocDone:
            _fail("the source has no function section (a # heading ending in Functions)")
        self.footer(doc.meta["footer"])
        props = self.doc.core_properties
        props.title = doc.meta["title"] + ": " + doc.meta["subtitle"]
        props.subject = doc.meta["subtitle"]
        props.author = ""
        props.last_modified_by = ""
        props.comments = ""
        props.keywords = ""
        stamp = datetime.datetime.fromisoformat(doc.meta["date"])
        props.created = stamp
        props.modified = stamp
        props.revision = 1

    def save(self, path):
        self.doc.save(path)


def _systemPython():
    """/usr/bin/python3 if it can import uno, else None."""
    python = shutil.which("python3", path="/usr/bin")
    if python is None:
        return None
    result = subprocess.run([python, "-c", "import uno"], capture_output=True)
    return python if result.returncode == 0 else None


def main():
    parser = argparse.ArgumentParser(
        description="Build Movie Functions.docx and .pdf from movie-functions.md.",
        epilog="Needs python-docx (requirements-dev.txt) and, for the PDF: "
               "sudo apt install " + APT_PACKAGES,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-pdf", action="store_true",
                        help="write only the .docx, without LibreOffice")
    args = parser.parse_args()

    try:
        doc = refdoc.parse()
    except refdoc.RefDocError as error:
        _fail("%s: %s\nNo files were written." % (os.path.basename(refdoc.SOURCE), error))
    try:
        import docx  # noqa: F401
    except ImportError:
        _fail("python-docx is missing: venv/bin/pip install -r "
              "contrib/movie/requirements-dev.txt")

    writer = Writer(TEMPLATE)
    writer.document(doc)
    writer.save(DOCX)
    print("wrote", DOCX, flush=True)
    if refdoc.PLACEHOLDER in doc.meta["footer"]:
        print("warning: the footer is still the placeholder %r; set footer: in "
              "the front matter of %s" % (doc.meta["footer"], refdoc.SOURCE), file=sys.stderr)

    if args.no_pdf:
        return
    python = _systemPython()
    if python is None or shutil.which("soffice") is None:
        _fail("cannot make the PDF: LibreOffice or python3-uno is missing.\n"
              "Install them with: sudo apt install " + APT_PACKAGES + "\n"
              + PDF + " was not updated.")
    result = subprocess.run([python, os.path.join(DOCS_DIR, "docx2pdf.py"), DOCX, PDF])
    if result.returncode:
        _fail("docx2pdf.py failed; " + PDF + " was not updated.")
    print("wrote", PDF)


if __name__ == "__main__":
    main()
