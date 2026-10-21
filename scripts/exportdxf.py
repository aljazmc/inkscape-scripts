from common import export, load_project

document, output = load_project("build")

export(document, output + ".dxf",
       extension="org.ekips.output.dxf_outlines")
