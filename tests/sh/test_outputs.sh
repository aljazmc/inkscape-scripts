#!/bin/bash
#
# project.sh names its outputs as the README says, and its clean commands
# remove exactly those: build/<project>.<format>, build/<project>.svg for the
# plain SVG of gsvg, and svg/<project>.svg for the Inkscape SVG.
#
# Runs in a sandbox (see lib.sh), so it never touches the real build/ or svg/.
# Run from anywhere: bash tests/sh/test_outputs.sh

# shellcheck source=tests/sh/lib.sh
. "$(dirname "$0")/lib.sh"
sandbox

# expect_outputs <project> <format> <file>: clean removes the file and no other
expect_outputs() {

    mkdir -p build svg
    touch "$3" build/keep.png svg/keep.svg build/nature-fern01.pdf
    ./project.sh "$1" "$2" clean > /dev/null 2>&1
    if [ -e "$3" ]; then
        fail "./project.sh $1 $2 clean should remove $3"
    elif [ ! -e build/keep.png ] || [ ! -e svg/keep.svg ] || [ ! -e build/nature-fern01.pdf ]; then
        fail "./project.sh $1 $2 clean removed other files"
    else
        pass "$1 $2 -> $3"
    fi
    rm -rf build svg

}

expect_outputs cyberpunk-butterfly00 png build/cyberpunk-butterfly00.png
expect_outputs cyberpunk-butterfly00 pdf build/cyberpunk-butterfly00.pdf
expect_outputs cyberpunk-butterfly00 gsvg build/cyberpunk-butterfly00.svg
expect_outputs cyberpunk-butterfly00 svg svg/cyberpunk-butterfly00.svg
expect_outputs cyberpunk-butterfly00 svgz build/cyberpunk-butterfly00.svgz
expect_outputs steampunk-gear02 tiff build/steampunk-gear02.tiff

# the plain and the Inkscape SVG don't clash
mkdir -p build svg
touch build/cyberpunk-butterfly00.svg svg/cyberpunk-butterfly00.svg
./project.sh cyberpunk-butterfly00 gsvg clean > /dev/null 2>&1
check "gsvg clean keeps the Inkscape SVG" [ -e svg/cyberpunk-butterfly00.svg ]
rm -rf build svg

# <project> clean removes every output of that project
mkdir -p build svg
while IFS= read -r format; do
    case "$format" in
        gsvg) touch build/cyberpunk-butterfly00.svg ;;
        *) touch "build/cyberpunk-butterfly00.$format" ;;
    esac
done < <(formats)
touch svg/cyberpunk-butterfly00.svg build/nature-fern01.png
./project.sh cyberpunk-butterfly00 clean > /dev/null 2>&1
check "<project> clean removes all its outputs" \
    [ -z "$(find build svg -name 'cyberpunk-butterfly00*')" ]
check "<project> clean keeps other projects' outputs" [ -e build/nature-fern01.png ]

./project.sh clean > /dev/null 2>&1
check "clean removes build/" [ ! -e build ]
check "clean removes svg/" [ ! -e svg ]

finish
