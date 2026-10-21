from common import export_raster, load_project

document, output = load_project("build")

export_raster(document, output + ".jpg", "RGB", "JPEG",
              quality=90,
              optimize=True,
              progressive=True)
