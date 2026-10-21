import importlib
import os
import subprocess
import sys
import tempfile

from PIL import Image

scripts_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(scripts_dir)


def load_project(target):
    """Build the SVG document of the project named by the PROJECT environment
    variable and return it with the output path (without extension) inside
    the root-level target directory.

    A project scripts/<theme>-<name>/ must provide <name>.py with a <name>()
    function returning the SVG document as a string, e.g.
    scripts/cyberpunk-butterfly00/butterfly00.py:butterfly00().
    """
    project = os.environ.get("PROJECT")
    if not project:
        sys.exit("usage: PROJECT=<project> PYTHONPATH=scripts "
                 "python3 <script>")

    project_dir = os.path.join(scripts_dir, project)
    if not os.path.isdir(project_dir):
        sys.exit(f"project not found: {project_dir}")

    name = project.rsplit("-", 1)[-1]
    sys.path.insert(0, project_dir)
    document = getattr(importlib.import_module(name), name)()

    target_dir = os.path.join(root_dir, target)
    os.makedirs(target_dir, exist_ok=True)

    return document, os.path.join(target_dir, project)


def export(document, filepath, extension=None, **settings):
    """Run an Inkscape export non-interactively, piping the document in.

    extension is the output extension id, needed when several extensions
    write the same file type (e.g. DXF R12 and R14). Keyword arguments are
    --export-* options, with "_" standing for "-", e.g. text_to_path=True
    adds "--export-text-to-path" and dpi=300 adds "--export-dpi=300".
    """
    args = ["inkscape", "--pipe", "--export-overwrite",
            f"--export-filename={filepath}"]
    if extension:
        args.append(f"--export-extension={extension}")
    for key, value in settings.items():
        option = "--export-" + key.replace("_", "-")
        args.append(option if value is True else f"{option}={value}")

    if os.path.exists(filepath):
        os.remove(filepath)

    # Inkscape exits with 0 even when an export fails, so check the file
    result = subprocess.run(args, input=document.encode(), capture_output=True)
    if result.returncode != 0 or not os.path.isfile(filepath):
        sys.exit(f"inkscape export failed for {filepath}:\n"
                 + result.stderr.decode(errors="replace"))


def export_raster(document, filepath, mode, image_format, **settings):
    """Render the document to PNG with Inkscape and convert it with Pillow.

    Inkscape's own JPEG, TIFF and WebP outputs fail from the command line,
    so this does what they do. Keyword arguments are Pillow save settings.
    """
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "render.png")
        export(document, png)
        with Image.open(png) as image:
            image.convert(mode).save(filepath, image_format,
                                     dpi=image.info.get("dpi", (96, 96)),
                                     **settings)
