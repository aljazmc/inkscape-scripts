# inkscape-scripts

[![CI](https://github.com/aljazmc/inkscape-scripts/actions/workflows/ci.yml/badge.svg)](https://github.com/aljazmc/inkscape-scripts/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Inkscape 1.x](https://img.shields.io/badge/Inkscape-1.x-000000?logo=inkscape&logoColor=white)](https://inkscape.org/)
[![Python 3](https://img.shields.io/badge/Python-3-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![SVG](https://img.shields.io/badge/SVG-ElementTree-ffb13b?logo=svg&logoColor=white)](https://docs.python.org/3/library/xml.etree.elementtree.html)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ShellCheck](https://img.shields.io/badge/ShellCheck-checked-4eaa25?logo=gnubash&logoColor=white)](https://www.shellcheck.net/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-fe5196?logo=conventionalcommits&logoColor=white)](https://www.conventionalcommits.org/)

Vector drawings written as code. Python scripts draw SVG documents with the
standard library, and a shell script exports them with Inkscape to PNG,
PDF, EPS, plain SVG, CAD, office, LaTeX and more, 24 formats in all.

![cyberpunk-butterfly00: a neon butterfly over a synthwave grid and a striped sun](gallery/cyberpunk-butterfly00.svg)

## Features

- **Drawings from code.** A project returns an SVG document built with
  Python's `xml.etree.ElementTree`, with Inkscape layers, gradients and
  glow filters.
- **24 outputs.** Raster images, print formats, plain and compressed SVG,
  DXF for CAD, HPGL for plotters, LaTeX drawing commands, office and
  animation formats, a GIMP palette and Inkscape SVG to keep editing.
- **Honest about failures.** Inkscape exits with 0 even when an export
  fails, so the scripts check that the file was written.
- **Workarounds built in.** Where Inkscape's own exporter fails from the
  command line, as for `jpg`, `tiff` and `webp`, the scripts render a PNG
  and convert it with Pillow.
- **The reference drawing.** The butterfly here is redrawn as a raster
  painting in [gimp-scripts](https://github.com/aljazmc/gimp-scripts) and
  as an animated 3D scene in
  [blender-scripts](https://github.com/aljazmc/blender-scripts), with the
  same coordinates.

## Quick start

```sh
git clone https://github.com/aljazmc/inkscape-scripts.git
cd inkscape-scripts
./project.sh cyberpunk-butterfly00 pdf
```

The PDF is written to `build/cyberpunk-butterfly00.pdf`.

## Requirements

| Requirement | Notes |
| --- | --- |
| Inkscape 1.x | `inkscape` on the `PATH` |
| Python 3 | with [Pillow](https://python-pillow.org/) for the `jpg`, `tiff` and `webp` outputs |

## Usage

```sh
./project.sh <project> <format>        # build one format
./project.sh <project> all             # build every format
./project.sh all <format>              # build every project
./project.sh <project> <format> clean  # remove one output
./project.sh <project> clean           # remove all outputs of a project
./project.sh clean                     # remove build/ and svg/
```

Outputs go to `build/<project>.<format>`, `gsvg` (plain SVG) to
`build/<project>.svg` and `svg` (Inkscape SVG) to `svg/<project>.svg`.
Existing outputs are skipped, so clean them to rebuild. The script can be
run from any directory. Without arguments, it prints the usage with every
format and the first ten projects.

### Formats

| Kind | Formats |
| --- | --- |
| Images | `png` `jpg` `tiff` `webp` |
| Print | `pdf` `eps` `ps` |
| SVG | `svg` `gsvg` `svgz` `zip` `tar` |
| Office and web | `odg` `emf` `wmf` `xaml` `fxg` `html` |
| CAD, plotters and code | `dxf` `hpgl` `tex` `pov` |
| Animation and palettes | `sif` `gpl` |

- `svg` saves Inkscape SVG, to open and edit the drawing in Inkscape;
  `gsvg` saves plain SVG for browsers and other programs, and `svgz` a
  compressed Inkscape SVG.
- `png` renders at 96 dpi, so a 1920×1080 drawing stays 1920×1080.
  Inkscape's own `jpg`, `tiff` and `webp` outputs fail from the command
  line, so these render a PNG and convert it with Pillow.
- `pdf`, `eps` and `ps` convert text to paths, so they need no fonts.
- `tex` writes LaTeX drawing commands for PSTricks, `zip` the SVG with
  everything it links to, `tar` each layer as a separate SVG, `gpl` a GIMP
  palette of its colors and `dxf` its outlines for CAD.
- `sif` (Synfig) drops the glow filters, which the Synfig exporter cannot
  read.

## How it works

```
project.sh ──> python3 scripts/export<format>.py
                                    │
                                    ▼
                             scripts/common.py
                                    │ load_project()
                                    ▼
          scripts/<project>/<name>.py: <name>() -> SVG string
                                    │ export()
                                    ▼
             inkscape --pipe --export-filename=build/<project>.<format>
```

- `project.sh` checks the arguments and runs `scripts/export<format>.py`
  (or `scripts/savesvg.py`) with `PROJECT=<project>` and
  `PYTHONPATH=scripts`.
- `scripts/common.py` imports the project and calls its function, then
  pipes the SVG into Inkscape with the `--export-*` options of the format.
  Inkscape exits with 0 even when an export fails, so it checks that the
  file was written.
- Each `scripts/export<format>.py` sets the options and, where several
  extensions write the same file type, the output extension for one format.

## Projects

A project is a folder `scripts/<theme>-<name>/` holding `<name>.py` with a
function `<name>()` that returns an SVG document as a string, built with
Python's `xml.etree.ElementTree`:

```
scripts/cyberpunk-butterfly00/
└── butterfly00.py   # butterfly00() returns the SVG document
```

The last part of the folder name is the module and function name, so it
must be a valid Python name. A project needs nothing outside its folder.

`cyberpunk-butterfly00` is a 1920×1080 neon butterfly over a synthwave grid
and a striped sun, drawn in Inkscape layers with gradients and Gaussian
blur glow filters. It is the reference for the raster version in
[gimp-scripts](https://github.com/aljazmc/gimp-scripts) and the animated 3D
version in [blender-scripts](https://github.com/aljazmc/blender-scripts),
which keep its coordinates. The drawing above was exported with
`./project.sh cyberpunk-butterfly00 gsvg`.

Themes such as `cyberpunk`, `steampunk`, `nature` and historical eras are
work in progress and kept out of the repository by `.gitignore` until they
are ready.

## Tests

```sh
for test in tests/sh/test_*.sh; do bash "$test"; done   # project.sh
python3 -m unittest discover tests/py                   # the scripts and the drawings
```

The tests are split by language: `tests/sh/` tests `project.sh` with bash,
`tests/py/` tests the Python scripts and the drawings they build. None of
them writes outputs into the repository.

The tests of `project.sh` run it in a temporary sandbox, with a few fake
projects and stand-ins for `python3` and `inkscape` (see
`tests/sh/lib.sh`), so they draw nothing and never touch `build/` or `svg/`:

- `tests/sh/test_project.sh` checks that `project.sh` rejects bad arguments
  with its usage and exit code 1.
- `tests/sh/test_formats.sh` checks that the formats of `project.sh`, the
  exporters in `scripts/` and this README agree: every format has an
  exporter that writes its own file, every exporter is listed, the Formats
  table names every format, and the count of formats is right.
- `tests/sh/test_outputs.sh` checks the names of the outputs, as described
  under Usage, through the `clean` commands; the plain SVG of `gsvg` and the
  Inkscape SVG of `svg` share a name in different folders.
- `tests/sh/test_run.sh` checks that `project.sh` runs the right script
  with the project in `PROJECT` and `scripts/` first on the `PYTHONPATH`,
  for one project and for `all`, from any directory; that it skips existing
  outputs, reports a failed export with exit code 1 and stops when
  `inkscape` or `python3` is missing.

The Python tests build every project as `project.sh` does, in a separate
Python process. `tests/py/test_common.py` and `tests/py/test_document.py`
need only Python; the others need Inkscape and Pillow and are skipped
without them (see `tests/py/drawing.py`):

- `tests/py/test_common.py` checks that `export()` turns its settings into
  Inkscape's `--export-*` options, with a stand-in for Inkscape.
- `tests/py/test_document.py` reads the SVG document without Inkscape: it is
  sized in pixels with a matching `viewBox`, its ids are unique, every
  `url(#...)` and `href` reaches an element (a broken one silently drops a
  gradient, filter or clip), everything is drawn in labelled Inkscape
  layers, colors are valid, there are no `nan` or `inf` numbers, and every
  build gives the same document.
- `tests/py/test_render.py` renders the drawing with Inkscape at a quarter
  of its size and checks the pixels: the right size, the page covered,
  neither black nor washed out, with contrast; that hiding any layer
  visibly changes the picture (a layer that doesn't is covered or off the
  page); and that the drawing in `gallery/` still matches the project.
- `tests/py/test_exports.py` runs every export script on a temporary copy
  of `scripts/` and checks each file by what is inside it: images at
  1920×1080, a PDF 1.5 header, the EPS and PostScript bounding box in
  points, SVG that parses (plain SVG without editor data, Inkscape SVG with
  its layers), one SVG per layer in the `tar`, the ODF manifest of the
  `odg`, the EMF and WMF signatures, complete DXF and HPGL, PSTricks,
  POV-Ray and canvas code, and a GIMP palette with every color of the
  drawing. Every format needs a check of its own, so a new format can't go
  untested. It takes about 20 seconds a project.

Lint the code with [ShellCheck](https://www.shellcheck.net/) and
[Ruff](https://docs.astral.sh/ruff/):

```sh
shellcheck project.sh tests/sh/*.sh
ruff check .
```

GitHub Actions runs both on every push and pull request, see
[.github/workflows/lint.yml](.github/workflows/lint.yml).

## License

The scripts are licensed under the [MIT License](LICENSE). The files in
`gallery/` were made with them and are under the same license.

The scripts drive software that is not part of this repository and has
licenses of its own:

- [Inkscape](https://inkscape.org/about/license/) is free software under
  the GNU General Public License, version 2 or later, with some parts under
  version 3 or later. The scripts only run Inkscape as a separate program.
  Whatever you draw or export with Inkscape is yours, and the GPL does not
  apply to it.
- [Pillow](https://github.com/python-pillow/Pillow/blob/main/LICENSE) is
  licensed under the MIT-CMU (HPND) license.
