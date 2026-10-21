from common import export_raster, load_project

document, output = load_project("build")

export_raster(document, output + ".tiff", "RGBA", "TIFF",
              compression="tiff_lzw")
