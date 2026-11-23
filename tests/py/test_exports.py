"""Every export script writes a valid file of its format, checked by what is
inside it, not just that it exists: images at the drawing's size, PDF and
PostScript with the right header and page, SVG that parses, archives with the
right contents, office and CAD files with their signatures, and a palette
holding every color of the drawing. Run: python3 -m unittest discover tests/py

The exports run on a temporary copy of scripts/, as project.sh runs them, so
nothing is written into the repository. They take about 20 seconds a
project. Needs Inkscape on the PATH and Pillow; skipped without them.
"""
import gzip
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import drawing

PLAIN_SVG_FORBIDDEN = ("inkscape.org", "sodipodi")


def formats():
    """The FORMATS of project.sh, and svg."""
    text = (drawing.ROOT / "project.sh").read_text()
    listed = re.search(r"^FORMATS=\((.*?)^\)", text, re.MULTILINE | re.DOTALL).group(1)
    return listed.split() + ["svg"]


def size(root):
    return tuple(round(float(re.sub("px$", "", root.get(k)))) for k in ("width", "height"))


def colors(root):
    """Every #rrggbb color the document uses, upper case."""
    found = set()
    for match in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", ET.tostring(root, encoding="unicode")):
        if len(match) == 3:
            match = "".join(c * 2 for c in match)
        found.add("#" + match.upper())
    return found


def local(tag):
    return tag.rsplit("}", 1)[-1]


class Checks:
    """One method per format: check_<format>(path, root) raises on a bad file."""

    def __init__(self, test):
        self.t = test

    def image(self, path, root, kind):
        from PIL import Image
        with Image.open(path) as image:
            self.t.assertEqual(image.format, kind)
            self.t.assertEqual(image.size, size(root), "the png export renders at 96 dpi")

    def check_png(self, path, root):
        self.image(path, root, "PNG")

    def check_jpg(self, path, root):
        self.image(path, root, "JPEG")

    def check_tiff(self, path, root):
        self.image(path, root, "TIFF")

    def check_webp(self, path, root):
        self.image(path, root, "WEBP")

    def check_pdf(self, path, root):
        data = path.read_bytes()
        self.t.assertTrue(data.startswith(b"%PDF-1.5"), "a PDF 1.5 header")
        self.t.assertTrue(data.rstrip().endswith(b"%%EOF"), "a complete PDF")

    def postscript(self, path, root, header):
        text = path.read_bytes().decode("latin-1")
        self.t.assertTrue(text.startswith(header), f"starts with {header}")
        box = re.search(r"^%%BoundingBox: (\d+) (\d+) (\d+) (\d+)", text, re.MULTILINE)
        self.t.assertIsNotNone(box, "a bounding box")
        x0, y0, x1, y1 = map(int, box.groups())
        # 96 pixels an inch, 72 points an inch
        width, height = (v * 72 / 96 for v in size(root))
        self.t.assertLessEqual(abs(x1 - x0 - width), 2, f"bounding box {box.group(0)}")
        self.t.assertLessEqual(abs(y1 - y0 - height), 2, f"bounding box {box.group(0)}")
        self.t.assertIn("%%EOF", text[-200:], "a complete file")

    def check_eps(self, path, root):
        self.postscript(path, root, "%!PS-Adobe-3.0 EPSF")

    def check_ps(self, path, root):
        self.postscript(path, root, "%!PS-Adobe-3.0")

    def svg(self, data, root):
        exported = ET.fromstring(data)
        self.t.assertEqual(local(exported.tag), "svg")
        self.t.assertEqual(size(exported), size(root))
        return exported

    def check_svg(self, path, root):
        # Inkscape SVG keeps the layers, to go on editing
        exported = self.svg(path.read_bytes(), root)
        label = f"{{{drawing.INKSCAPE_NS}}}label"
        self.t.assertEqual([c.get(label) for c in exported if c.get(label)],
                           [c.get(label) for c in root if c.get(label)], "the layers")

    def check_gsvg(self, path, root):
        text = path.read_text()
        self.svg(text.encode(), root)
        for namespace in PLAIN_SVG_FORBIDDEN:
            self.t.assertNotIn(namespace, text, "plain SVG has no editor data")

    def check_svgz(self, path, root):
        self.svg(gzip.decompress(path.read_bytes()), root)

    def check_zip(self, path, root):
        with zipfile.ZipFile(path) as archive:
            self.t.assertIsNone(archive.testzip())
            svgs = [n for n in archive.namelist() if n.endswith(".svg")]
            self.t.assertEqual(len(svgs), 1, f"one SVG in {archive.namelist()}")
            self.svg(archive.read(svgs[0]), root)

    def check_tar(self, path, root):
        label = f"{{{drawing.INKSCAPE_NS}}}label"
        with tarfile.open(path) as archive:
            names = archive.getnames()
            self.t.assertEqual(names, [c.get(label) + ".svg" for c in root if c.get(label)],
                               "one SVG for each layer")
            for name in names:
                self.svg(archive.extractfile(name).read(), root)

    def check_odg(self, path, root):
        with zipfile.ZipFile(path) as archive:
            self.t.assertIsNone(archive.testzip())
            manifest = archive.read("META-INF/manifest.xml").decode()
            self.t.assertIn("application/vnd.oasis.opendocument.graphics", manifest)
            content = ET.fromstring(archive.read("content.xml"))
            self.t.assertEqual(local(content.tag), "document-content")
            self.t.assertTrue(any("drawing" in e.tag for e in content.iter()), "drawing content")

    def check_emf(self, path, root):
        data = path.read_bytes()
        self.t.assertEqual(data[:4], b"\x01\x00\x00\x00", "an EMF header record")
        self.t.assertEqual(data[40:44], b" EMF", "the EMF signature")

    def check_wmf(self, path, root):
        self.t.assertEqual(path.read_bytes()[:4], b"\xd7\xcd\xc6\x9a", "a placeable WMF")

    def check_dxf(self, path, root):
        lines = [line.strip() for line in path.read_text(errors="replace").splitlines()]
        self.t.assertEqual(lines[:2], ["0", "SECTION"])
        self.t.assertEqual(lines[-1], "EOF", "a complete DXF")
        self.t.assertIn("ENTITIES", lines)

    def check_hpgl(self, path, root):
        text = path.read_text()
        self.t.assertTrue(text.startswith("IN;"), "HPGL starts with IN;")
        self.t.assertIn("PD", text, "pen down: something is drawn")

    def check_tex(self, path, root):
        text = path.read_text()
        self.t.assertIn(r"\begin{pspicture}(%d,%d)" % size(root), text)
        self.t.assertIn(r"\end{pspicture}", text)

    def check_pov(self, path, root):
        text = path.read_text()
        self.t.assertIn("#declare", text, "POV-Ray declarations")
        self.t.assertIn("prism", text, "shapes as prisms")

    def check_html(self, path, root):
        text = path.read_text()
        self.t.assertRegex(text, r"<canvas[^>]*width=.%d.[^>]*height=.%d." % size(root))
        self.t.assertIn("getContext", text, "the drawing code")

    def xml(self, path, tag):
        exported = ET.parse(path).getroot()
        self.t.assertEqual(local(exported.tag), tag)
        self.t.assertGreater(len(list(exported.iter())), 10, "something drawn")
        return exported

    def check_xaml(self, path, root):
        self.xml(path, "ResourceDictionary")

    def check_fxg(self, path, root):
        self.xml(path, "Graphic")

    def check_sif(self, path, root):
        canvas = self.xml(path, "canvas")
        self.t.assertEqual((round(float(canvas.get("width"))), round(float(canvas.get("height")))),
                           size(root))

    def check_gpl(self, path, root):
        lines = path.read_text().splitlines()
        self.t.assertEqual(lines[0], "GIMP Palette")
        palette = {m.group(1).upper() for m in
                   (re.search(r"(#[0-9A-Fa-f]{6})\s*$", line) for line in lines) if m}
        missing = colors(root) - palette
        self.t.assertEqual(missing, set(), "colors of the drawing missing from the palette")


def output(tmp, project, format):
    if format == "svg":
        return Path(tmp, "svg", project + ".svg")
    return Path(tmp, "build", project + "." + ("svg" if format == "gsvg" else format))


@unittest.skipUnless(drawing.INKSCAPE and drawing.pillow(), "needs inkscape and Pillow")
class ExportTest(unittest.TestCase):

    def test_every_format_has_a_check(self):
        missing = [f for f in formats() if not hasattr(Checks, "check_" + f)]
        self.assertEqual(missing, [], "formats without a check in test_exports.py")

    def test_exports_are_valid(self):
        checks = Checks(self)
        self.assertTrue(drawing.projects(), "no projects")
        for project in drawing.projects():
            root = drawing.parse(drawing.document(project))
            with tempfile.TemporaryDirectory() as tmp:
                shutil.copytree(drawing.SCRIPTS, Path(tmp, "scripts"),
                                ignore=shutil.ignore_patterns("__pycache__"))
                for format in formats():
                    with self.subTest(project=project, format=format):
                        script = "savesvg.py" if format == "svg" else f"export{format}.py"
                        result = subprocess.run(
                            [sys.executable, f"scripts/{script}"], cwd=tmp,
                            capture_output=True, text=True, timeout=300,
                            env={**os.environ, "PROJECT": project, "PYTHONPATH": "scripts",
                                 "PYTHONDONTWRITEBYTECODE": "1"})
                        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
                        path = output(tmp, project, format)
                        self.assertTrue(path.is_file(), f"no {path.name}")
                        self.assertGreater(path.stat().st_size, 0, f"{path.name} is empty")
                        getattr(checks, "check_" + format)(path, root)


if __name__ == "__main__":
    unittest.main()
