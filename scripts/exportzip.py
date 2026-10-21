from common import export, load_project

document, output = load_project("build")

export(document, output + ".zip",
       extension="org.inkscape.output.compressed_media")
