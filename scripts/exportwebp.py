from common import export_raster, load_project

document, output = load_project("build")

export_raster(document, output + ".webp", "RGBA", "WEBP",
              quality=90,
              method=6)
