#!/bin/bash
#
# project.sh runs the right export script for each request, with the project
# in PROJECT and scripts/ on the PYTHONPATH, for one project or all of them,
# and from any directory. It skips outputs that exist, reports a failed export
# with exit code 1, and stops when a program it needs is missing.
#
# Runs in a sandbox (see lib.sh) with a stand-in python3, so nothing is drawn.
# Run from anywhere: bash tests/sh/test_run.sh

# shellcheck source=tests/sh/lib.sh
. "$(dirname "$0")/lib.sh"
sandbox

# expect_calls <description> <expected calls.log> -- <project.sh arguments>
expect_calls() {

    local description=$1 expected=$2
    shift 3
    : > calls.log
    ./project.sh "$@" > output.log 2>&1
    if [ "$(cat calls.log)" = "$expected" ]; then
        pass "$description"
    else
        fail "$description: ./project.sh $* ran"$'\n'"$(cat calls.log)"$'\n'"expected"$'\n'"$expected"
    fi

}

expect_calls "one project, one format" \
    "PROJECT=cyberpunk-butterfly00 PYTHONPATH=scripts python3 scripts/exportpdf.py" \
    -- cyberpunk-butterfly00 pdf

expect_calls "svg runs savesvg.py" \
    "PROJECT=nature-fern01 PYTHONPATH=scripts python3 scripts/savesvg.py" \
    -- nature-fern01 svg

expect_calls "all runs every project, sorted" \
    "PROJECT=cyberpunk-butterfly00 PYTHONPATH=scripts python3 scripts/exportpng.py
PROJECT=nature-fern01 PYTHONPATH=scripts python3 scripts/exportpng.py
PROJECT=steampunk-gear02 PYTHONPATH=scripts python3 scripts/exportpng.py" \
    -- all png

: > calls.log
PYTHONPATH=/elsewhere ./project.sh steampunk-gear02 eps > /dev/null 2>&1
check "an existing PYTHONPATH is kept after scripts/" \
    grep -qx "PROJECT=steampunk-gear02 PYTHONPATH=scripts:/elsewhere python3 scripts/exporteps.py" calls.log

: > calls.log
(cd / && "$SANDBOX/project.sh" nature-fern01 png > /dev/null 2>&1)
check "it runs from any directory" \
    grep -qx "PROJECT=nature-fern01 PYTHONPATH=scripts python3 scripts/exportpng.py" calls.log

: > calls.log
./project.sh steampunk-gear02 all > /dev/null 2>&1
count=$(formats | wc -l)
check "<project> all runs every format and svg ($((count + 1)) runs)" \
    [ "$(wc -l < calls.log)" -eq $((count + 1)) ]
check "and each of them once" [ "$(sort -u calls.log | wc -l)" -eq $((count + 1)) ]

mkdir -p build
touch build/nature-fern01.webp
expect_calls "an existing output is skipped" "" -- nature-fern01 webp
check "and says so" grep -q "Skipping build/nature-fern01.webp" output.log
rm -rf build

PYTHON_EXIT=1 ./project.sh all png > output.log 2>&1
code=$?
check "a failed export exits with 1" [ "$code" -eq 1 ]
check "and names the project" grep -q "FAILED: exportpng for nature-fern01" output.log
check "and goes on with the other projects" [ "$(grep -c FAILED output.log)" -eq 3 ]

# only the stand-ins and the basic tools project.sh uses on the PATH
mkdir tools
for tool in bash find sort head paste dirname; do
    ln -s "$(command -v "$tool")" "tools/$tool"
done
for missing in inkscape python3; do
    mv "bin/$missing" "bin/$missing.away"
    PATH="$SANDBOX/bin:$SANDBOX/tools" ./project.sh cyberpunk-butterfly00 png > output.log 2>&1
    code=$?
    mv "bin/$missing.away" "bin/$missing"
    check "without $missing it exits with 1" [ "$code" -eq 1 ]
    check "and names $missing" grep -q "$missing is required" output.log
done

finish
