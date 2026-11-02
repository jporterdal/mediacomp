"""Convert a .docx to PDF with LibreOffice, refreshing its table of contents.

Runs under the system Python (/usr/bin/python3), because python3-uno is a
Debian package that the repo's venv cannot import. build.py starts it:

    /usr/bin/python3 docx2pdf.py <input.docx> <output.pdf>

It starts its own headless soffice with a throw-away profile in a new
temporary folder, so a running LibreOffice or a locked profile cannot get in
the way. If soffice does not finish within TIMEOUT seconds it is killed. The
temporary folder is left in place and its path printed.
"""

import os
import subprocess
import sys
import tempfile
import threading
import time

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException

TIMEOUT = 120


def _props(**values):
    props = []
    for name, value in values.items():
        prop = PropertyValue()
        prop.Name = name
        prop.Value = value
        props.append(prop)
    return tuple(props)


def _connect(pipe, proc, deadline):
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    while True:
        try:
            return resolver.resolve(
                "uno:pipe,name=%s;urp;StarOffice.ComponentContext" % pipe)
        except NoConnectException:
            if proc.poll() is not None:
                raise RuntimeError("soffice exited with code %d before accepting "
                                   "a connection" % proc.returncode)
            if time.monotonic() > deadline:
                raise RuntimeError("soffice did not start within %d seconds" % TIMEOUT)
            time.sleep(0.5)


def convert(source, target, tempdir):
    pipe = "docx2pdf_%d" % os.getpid()
    profile = uno.systemPathToFileUrl(os.path.join(tempdir, "profile"))
    proc = subprocess.Popen(
        ["soffice", "--headless", "--invisible", "--nologo", "--norestore",
         "--nodefault", "-env:UserInstallation=" + profile,
         "--accept=pipe,name=%s;urp;StarOffice.ComponentContext" % pipe],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    watchdog = threading.Timer(TIMEOUT, proc.kill)
    watchdog.start()
    desktop = None
    try:
        ctx = _connect(pipe, proc, time.monotonic() + TIMEOUT)
        desktop = ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", ctx)
        doc = desktop.loadComponentFromURL(
            uno.systemPathToFileUrl(os.path.abspath(source)), "_blank", 0,
            _props(Hidden=True))
        if doc is None:
            raise RuntimeError("LibreOffice could not open " + source)
        try:
            # Twice: filling in the table of contents can move later pages.
            for _ in range(2):
                indexes = doc.getDocumentIndexes()
                for i in range(indexes.getCount()):
                    indexes.getByIndex(i).update()
                doc.refresh()
            partial = target + ".part"
            doc.storeToURL(uno.systemPathToFileUrl(os.path.abspath(partial)),
                           _props(FilterName="writer_pdf_Export"))
            os.replace(partial, target)
            return indexes.getCount()
        finally:
            doc.close(True)
    finally:
        if desktop is not None:
            try:
                desktop.terminate()
            except Exception:
                pass
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        watchdog.cancel()


def main():
    if len(sys.argv) != 3:
        print("usage: docx2pdf.py <input.docx> <output.pdf>", file=sys.stderr)
        sys.exit(2)
    tempdir = tempfile.mkdtemp(prefix="docx2pdf-")
    try:
        count = convert(sys.argv[1], sys.argv[2], tempdir)
    except Exception as error:
        print("docx2pdf.py: %s" % error, file=sys.stderr)
        sys.exit(1)
    finally:
        print("docx2pdf.py: LibreOffice profile left in " + tempdir)
    if count == 0:
        print("docx2pdf.py: warning: no table of contents was found to update",
              file=sys.stderr)


if __name__ == "__main__":
    main()
