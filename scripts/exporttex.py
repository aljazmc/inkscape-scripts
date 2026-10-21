from common import export, load_project

document, output = load_project("build")

export(document, output + ".tex",
       extension="org.inkscape.output.latex")
