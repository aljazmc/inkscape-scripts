#!/bin/bash
#
# The formats in project.sh, the exporters in scripts/ and the README agree:
# every format has an exporter that writes its own file, every exporter is
# listed, the README's Formats table names every format, and its count of
# formats is right.
#
# Run from anywhere: bash tests/sh/test_formats.sh

# shellcheck source=tests/sh/lib.sh
. "$(dirname "$0")/lib.sh"
cd "$ROOT" || exit 1

mapfile -t known < <(formats)

if [ "${#known[@]}" -lt 20 ]; then
    fail "read the FORMATS of project.sh, got ${#known[@]}: ${known[*]}"
fi

for format in "${known[@]}"; do
    script="scripts/export$format.py"
    if [ ! -f "$script" ]; then
        fail "$format has no $script"
        continue
    fi
    # gsvg is plain SVG, written as <project>.svg in build/
    extension=".$format"
    [ "$format" = "gsvg" ] && extension=".svg"
    check "$script writes $extension" grep -qF "output + \"$extension\"" "$script"
    check "$script writes into build/" grep -qF 'load_project("build")' "$script"
    check "the README lists $format" grep -qE "^\|.*\`$format\`" README.md
done

for script in scripts/export*.py; do
    format=${script#scripts/export}
    format=${format%.py}
    listed=no
    for name in "${known[@]}"; do
        [ "$name" = "$format" ] && listed=yes
    done
    check "$script is in the FORMATS of project.sh" [ "$listed" = yes ]
done

check "scripts/savesvg.py saves Inkscape SVG into svg/" \
    grep -qF 'load_project("svg")' scripts/savesvg.py
check "the README lists svg" grep -qE "^\|.*\`svg\`" README.md

# every format and the Inkscape SVG
outputs=$(( ${#known[@]} + 1 ))
readme=$(tr '\n' ' ' < README.md)
check "the README counts $outputs formats" grep -qE "$outputs formats in all.*\*\*$outputs outputs\.\*\*" <<< "$readme"

finish
