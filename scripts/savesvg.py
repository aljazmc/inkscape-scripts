from common import export, load_project

document, output = load_project("svg")

export(document, output + ".svg",
       extension="org.inkscape.output.svg.inkscape")
