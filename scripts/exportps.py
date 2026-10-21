from common import export, load_project

document, output = load_project("build")

export(document, output + ".ps",
       ps_level=3,
       text_to_path=True)
