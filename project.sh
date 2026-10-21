#!/bin/bash

FORMATS=(
    dxf emf eps fxg gpl gsvg hpgl html jpg odg pdf png pov ps sif svgz tar
    tex tiff webp wmf xaml zip
)

status=0

cd "$(dirname "$0")" || exit 1

require() {

    local bin
    if bin=$(command -v "$1"); then
        echo "$1 found at: $bin"
    else
        echo "$1 is required but was not found" >&2
        exit 1
    fi

}

projects() {

    find scripts -mindepth 1 -maxdepth 1 -type d ! -name __pycache__ -printf '%f\n' | sort

}

output() {

    case "$2" in
        svg) echo "svg/$1.svg" ;;
        gsvg) echo "build/$1.svg" ;;
        *) echo "build/$1.$2" ;;
    esac

}

run() {

    local script file
    [ "$2" = "svg" ] && script="savesvg" || script="export$2"
    file=$(output "$1" "$2")

    if [ -e "$file" ]; then
        echo "Skipping $file (already exists)"
        return
    fi

    PROJECT="$1" PYTHONPATH="scripts${PYTHONPATH:+:$PYTHONPATH}" python3 "scripts/$script.py" || {
        echo "FAILED: $script for $1" >&2
        status=1
    }

}

remove() {

    local file
    file=$(output "$1" "$2")

    if [ -e "$file" ]; then
        rm -f "$file"
        echo "Removed $file"
    fi

}

process() {

    local format
    if [ "$2" = "all" ]; then
        for format in "${FORMATS[@]}" svg; do
            "$3" "$1" "$format"
        done
    else
        "$3" "$1" "$2"
    fi

}

clean() {

    rm -rf build svg

}

usage() {

    local IFS="|"
    echo "You should use: $0 clean" >&2
    echo "            or: $0 {all|<project>} {all|svg|${FORMATS[*]}}" >&2
    echo "            or: $0 {all|<project>} clean" >&2
    echo "            or: $0 {all|<project>} {svg|${FORMATS[*]}} clean" >&2
    echo "Projects: $(projects | paste -sd' ')" >&2
    exit 1

}

valid_format() {

    local format
    [ "$1" = "all" ] || [ "$1" = "svg" ] && return 0
    for format in "${FORMATS[@]}"; do
        [ "$1" = "$format" ] && return 0
    done
    return 1

}

[ "$1" = "clean" ] && [ $# -eq 1 ] && { clean; exit; }

if [ $# -eq 2 ] && [ "$2" = "clean" ]; then
    format="all"
    action="remove"
elif [ $# -eq 3 ] && [ "$3" = "clean" ]; then
    format="$2"
    action="remove"
elif [ $# -eq 2 ]; then
    format="$2"
    action="run"
else
    usage
fi

valid_format "$format" || usage

if [ "$1" = "all" ]; then
    mapfile -t targets < <(projects)
elif [ -d "scripts/$1" ]; then
    targets=("$1")
else
    usage
fi

[ "$action" = "run" ] && { require inkscape; require python3; }

for project in "${targets[@]}"; do
    process "$project" "$format" "$action"
done

exit "$status"
