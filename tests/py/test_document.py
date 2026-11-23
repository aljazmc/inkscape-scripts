"""Every project builds a sound SVG document, read without Inkscape: well
formed, sized in pixels with a matching viewBox, unique ids, every reference
to a gradient, filter or clip path resolving, every drawing element in an
Inkscape layer, valid colors and numbers, and the same document on every
build. Run: python3 -m unittest discover tests/py
"""
import re
import unittest

import drawing

URL = re.compile(r"url\(#([^)]+)\)")
COLOR = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$")
COLOR_PROPERTIES = ("fill", "stroke", "stop-color", "flood-color", "lighting-color", "color")
NAMED = {"none", "currentColor", "transparent", "inherit", "black", "white"}
NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
PATH = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|" + NUMBER.pattern + r"|[\s,]+")


def local(tag):
    return tag.rsplit("}", 1)[-1]


def properties(element):
    """The element's presentation attributes and style properties."""
    found = dict(element.attrib)
    for declaration in element.get("style", "").split(";"):
        if ":" in declaration:
            key, value = declaration.split(":", 1)
            found[key.strip()] = value.strip()
    return found


class DocumentTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.documents = {project: drawing.document(project) for project in drawing.projects()}

    def each(self):
        self.assertTrue(self.documents, "no projects")
        for project, text in self.documents.items():
            yield project, drawing.parse(text)

    def test_is_an_svg_sized_in_pixels(self):
        for project, root in self.each():
            with self.subTest(project=project):
                self.assertEqual(root.tag, f"{{{drawing.SVG}}}svg")
                width, height = root.get("width"), root.get("height")
                self.assertRegex(width or "", r"^\d+(\.\d+)?(px)?$", "width in pixels")
                self.assertRegex(height or "", r"^\d+(\.\d+)?(px)?$", "height in pixels")
                # so one user unit is one pixel, as the exports assume
                box = [float(v) for v in root.get("viewBox", "").replace(",", " ").split()]
                self.assertEqual(box, [0, 0, float(width.rstrip("px")), float(height.rstrip("px"))],
                                 "viewBox must be 0 0 width height")

    def test_ids_are_unique(self):
        for project, root in self.each():
            with self.subTest(project=project):
                ids = [e.get("id") for e in root.iter() if e.get("id")]
                repeated = sorted({i for i in ids if ids.count(i) > 1})
                self.assertEqual(repeated, [], "ids used twice")

    def test_references_resolve(self):
        # a broken url(#...) silently drops the gradient, filter or clip
        for project, root in self.each():
            with self.subTest(project=project):
                ids = {e.get("id") for e in root.iter() if e.get("id")}
                broken = set()
                for element in root.iter():
                    for key, value in properties(element).items():
                        broken |= {f"{key}: #{target}" for target in URL.findall(value)
                                   if target not in ids}
                    for key in (f"{{{drawing.XLINK}}}href", "href"):
                        target = element.get(key, "")
                        if target.startswith("#") and target[1:] not in ids:
                            broken.add(f"href: {target}")
                self.assertEqual(sorted(broken), [], "references to ids that don't exist")

    def test_drawing_is_in_labelled_layers(self):
        # so the layers show in Inkscape and the tar export splits them
        for project, root in self.each():
            with self.subTest(project=project):
                labels = []
                for child in root:
                    if local(child.tag) in ("defs", "metadata", "namedview", "title", "desc"):
                        continue
                    self.assertEqual(local(child.tag), "g", f"<{local(child.tag)}> outside the layers")
                    self.assertEqual(child.get(f"{{{drawing.INKSCAPE_NS}}}groupmode"), "layer",
                                     f"group {child.get('id')} is not a layer")
                    label = child.get(f"{{{drawing.INKSCAPE_NS}}}label")
                    self.assertTrue(label, f"layer {child.get('id')} has no label")
                    labels.append(label)
                self.assertTrue(labels, "no layers")
                self.assertEqual(len(labels), len(set(labels)), f"layer labels repeat: {labels}")

    def test_colors_are_valid(self):
        for project, root in self.each():
            with self.subTest(project=project):
                bad = []
                for element in root.iter():
                    for key, value in properties(element).items():
                        if key in COLOR_PROPERTIES and not value.startswith("url(") \
                                and value not in NAMED and not COLOR.match(value):
                            bad.append(f"{key}={value}")
                self.assertEqual(bad, [], "colors that aren't #rgb or #rrggbb")

    def test_numbers_are_finite(self):
        # Python writes nan and inf, which no SVG reader understands
        for project, root in self.each():
            with self.subTest(project=project):
                bad = []
                for element in root.iter():
                    for key, value in element.attrib.items():
                        if re.search(r"\b(nan|inf)\b", value, re.IGNORECASE):
                            bad.append(f"<{local(element.tag)} {local(key)}={value[:40]}>")
                    if local(element.tag) == "path":
                        rest = PATH.sub("", element.get("d", ""))
                        if rest:
                            bad.append(f"<path d> has {rest[:20]!r}")
                self.assertEqual(bad, [])

    def test_builds_the_same_document_every_time(self):
        for project, text in self.documents.items():
            with self.subTest(project=project):
                self.assertEqual(drawing.build(project), text,
                                 "a second build gave another document")


if __name__ == "__main__":
    unittest.main()
