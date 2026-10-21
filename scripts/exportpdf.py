from common import export, load_project

document, output = load_project("build")

export(document, output + ".pdf",
       pdf_version=1.5,
       text_to_path=True)
