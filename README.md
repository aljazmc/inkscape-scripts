# inkscape-scripts

Python scripts that draw vector images as SVG, and a shell script that
exports them with Inkscape to PNG, PDF, EPS, plain SVG, CAD, office and
about twenty other formats. Each drawing is a self-contained project in
`scripts/` with AI-generated code.

## Requirements

- Inkscape 1.x, with `inkscape` on the `PATH`
- Python 3, with [Pillow](https://python-pillow.org/) for the `jpg`,
  `tiff` and `webp` outputs

## Usage

```sh
./project.sh <project> <format>        # build one format
./project.sh <project> all             # build every format
./project.sh all <format>              # build every project
./project.sh <project> <format> clean  # remove one output
./project.sh <project> clean           # remove all outputs of a project
./project.sh clean                     # remove build/ and svg/
```

For example:

```sh
./project.sh cyberpunk-butterfly00 pdf
```

Outputs go to `build/<project>.<format>`, `gsvg` (plain SVG) to
`build/<project>.svg` and `svg` (Inkscape SVG) to `svg/<project>.svg`.
Existing outputs are skipped, so clean them to rebuild. The script can be
run from any directory. Without arguments, it prints the usage with every
format and the first ten projects.

### Formats

`dxf emf eps fxg gpl gsvg hpgl html jpg odg pdf png pov ps sif svgz tar
tex tiff webp wmf xaml zip svg`

- `svg` saves Inkscape SVG, to open and edit the drawing in Inkscape;
  `gsvg` saves plain SVG for browsers and other programs, and `svgz` a
  compressed Inkscape SVG.
- `png` renders at 96 dpi, so a 1920×1080 drawing stays 1920×1080.
  Inkscape's own `jpg`, `tiff` and `webp` outputs fail from the command
  line, so these render a PNG and convert it with Pillow.
- `pdf`, `eps` and `ps` convert text to paths, so they need no fonts.
- `tex` writes LaTeX drawing commands for PSTricks, `zip` the SVG with
  everything it links to, `tar` each layer as a separate SVG, `gpl` a
  GIMP palette of its colors and `dxf` its outlines for CAD.
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
  extensions write the same file type, the output extension for one
  format.

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

`cyberpunk-butterfly00` is a 1920×1080 neon butterfly over a synthwave
grid and a striped sun, drawn in Inkscape layers with gradients and
Gaussian blur glow filters. It is the reference for the raster version in
[gimp-scripts](https://github.com/aljazmc/gimp-scripts) and the animated
3D version in [blender-scripts](https://github.com/aljazmc/blender-scripts),
which keep its coordinates.

Themes such as `cyberpunk`, `steampunk`, `nature` and historical eras are
work in progress and kept out of the repository by `.gitignore` until they
are ready.

## Tests

```sh
bash tests/test_project.sh             # project.sh
python3 -m unittest discover tests     # the Python scripts
```

The tests need only bash and Python's standard library, and none of them
runs the application or writes outputs. `tests/test_project.sh` checks
that `project.sh` rejects bad arguments with its usage and exit code 1.
`tests/test_common.py` checks that `export()` turns its settings into
Inkscape's `--export-*` options, with a stand-in for Inkscape.

To lint the code with [ShellCheck](https://www.shellcheck.net/) and
[Ruff](https://docs.astral.sh/ruff/):

```sh
shellcheck project.sh tests/*.sh
ruff check .
```

GitHub Actions runs both on every push and pull request, see
[.github/workflows/lint.yml](.github/workflows/lint.yml).

## Gallery

`cyberpunk-butterfly00`, exported with `./project.sh cyberpunk-butterfly00 gsvg`:

![cyberpunk-butterfly00](gallery/cyberpunk-butterfly00.svg)

## License

The scripts are licensed under the MIT license, see [LICENSE](LICENSE).
The files in `gallery/` were made with them and are under the same
license.

The scripts drive software that is not part of this repository and has
licenses of its own:

- [Inkscape](https://inkscape.org/about/license/) is free software under
  the GNU General Public License, version 2 or later, with some parts
  under version 3 or later. The scripts only run Inkscape as a separate
  program. Whatever you draw or export with Inkscape is yours, and the
  GPL does not apply to it.
- [Pillow](https://github.com/python-pillow/Pillow/blob/main/LICENSE) is
  licensed under the MIT-CMU (HPND) license.
