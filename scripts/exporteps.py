from common import export, load_project

document, output = load_project("build")

export(document, output + ".eps",
       ps_level=3,
       text_to_path=True)
