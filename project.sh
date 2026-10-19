#!/bin/bash

FORMATS=(
    dxf emf eps fxg gpl hpgl html jpg odg pdf png pov ps sif svg svgz
    tar tex tiff webp wmf xaml xcf zip
)

require() {

    local bin
    if bin=$(command -v "$1"); then
        echo "$1 found at: $bin"
    else
        echo "$1 is required but was not found" >&2
        exit 1
    fi

}

run() {

    require inkscape
    require python3

    find scripts -maxdepth 2 -mindepth 2 -type f -name "$1" -exec {} \;

}

build() {

    run "*.py"

}

clean() {

    rm -rf build

}

export_format() {

    run "export$1.py"

}

save() {

    run "savesvg.py"

}

usage() {

    local IFS="|"
    echo "You should use: $0 {build|clean|save|${FORMATS[*]}}" >&2
    exit 1

}

cd "$(dirname "$0")" || exit 1

case "$1" in
    build|clean|save) "$1" ;;
    *)
        for format in "${FORMATS[@]}"; do
            [ "$1" = "$format" ] && { export_format "$1"; exit; }
        done
        usage
        ;;
esac
