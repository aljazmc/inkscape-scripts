from common import export, load_project

document, output = load_project("build")

export(document, output + ".png",
       dpi=96,
       png_compression=9)
