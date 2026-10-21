import re

from common import export, load_project

document, output = load_project("build")

# The Synfig exporter never reads <defs>, so it can't find any filter
document = re.sub(r' filter="url\(#[^)]*\)"', "", document)

export(document, output + ".sif")
