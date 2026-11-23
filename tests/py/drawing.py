"""Helpers for the tests: the projects, their SVG documents and Inkscape.

A project is built in its own Python process, as project.sh runs it, with its
output directory in a temporary folder, so nothing is written into the
repository. Not a test itself.
"""
import functools
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
INKSCAPE = shutil.which("inkscape")

SVG = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
XLINK = "http://www.w3.org/1999/xlink"

BUILD = """
import sys, tempfile
sys.path.insert(0, sys.argv[1])
from common import load_project
document, _ = load_project(tempfile.mkdtemp())
sys.stdout.write(document)
"""


def projects():
    """The projects: folders of scripts/ holding <name>.py, where <name> is
    the part of the folder name after its last hyphen."""
    return sorted(folder.name for folder in SCRIPTS.iterdir()
                  if folder.is_dir()
                  and (folder / (folder.name.rsplit("-", 1)[-1] + ".py")).is_file())


def build(project):
    """The project's SVG document, as a string, built afresh."""
    result = subprocess.run(
        [sys.executable, "-c", BUILD, str(SCRIPTS)],
        capture_output=True, text=True, cwd=ROOT,
        env={**os.environ, "PROJECT": project, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if result.returncode != 0:
        raise AssertionError(f"{project} failed to build:\n{result.stderr[-3000:]}")
    return result.stdout


@functools.cache
def document(project):
    """The project's SVG document, built once per test run."""
    return build(project)


def parse(text):
    return ET.fromstring(text.encode())


def render(svg_text, dpi=24, **options):
    """Render SVG text to PNG with Inkscape and return it as a Pillow image."""
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "render.png")
        args = [INKSCAPE, "--pipe", "--export-type=png", f"--export-filename={png}",
                f"--export-dpi={dpi}"]
        args += [f"--export-{key.replace('_', '-')}={value}" for key, value in options.items()]
        subprocess.run(args, input=svg_text.encode(), capture_output=True, check=True)
        with Image.open(png) as image:
            return image.convert("RGBA")


def pillow():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    sys.exit("a helper for the tests, not a test")
