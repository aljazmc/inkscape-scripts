from common import export, load_project

document, output = load_project("build")

export(document, output + ".svgz",
       extension="org.inkscape.output.svgz.inkscape")
