"""Every project renders a picture worth looking at, through Inkscape at a
quarter of its size: the right size, the page covered, neither black nor
washed out, with contrast, every layer adding something you can see, and the
gallery picture of the project up to date. Run: python3 -m unittest discover tests/py

Needs Inkscape on the PATH and Pillow; skipped without them.
"""
import re
import unittest

import drawing

DPI = 24  # a quarter of the 96 dpi of the png export
# share of fully transparent pixels: above, the page has holes
TRANSPARENT_MAX = 0.01
# mean luminance (0..255): below is black, above is washed out
DARK, BRIGHT = 5, 230
# standard deviation of luminance: below is a flat, featureless picture
CONTRAST_MIN = 10
# share of pixels that visibly change (by more than 16 of 255) when a layer is
# hidden: below, it adds nothing; a thin layer changes few pixels, but clearly
LAYER_MIN = 0.001
# mean difference from the picture in gallery/: above, the gallery is stale
GALLERY_MAX = 2.0


def luminance(image):
    from PIL import ImageStat
    return ImageStat.Stat(image.convert("L"))


def difference(a, b):
    from PIL import ImageChops
    return luminance(ImageChops.difference(a.convert("RGB"), b.convert("RGB"))).mean[0]


def changed(a, b):
    """Share of pixels that differ visibly between two pictures."""
    from PIL import ImageChops
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("L")
    return sum(d.histogram()[17:]) / (d.width * d.height)


def without_layer(text, layer_id):
    """The document with one layer hidden."""
    root = drawing.parse(text)
    for child in root:
        if child.get("id") == layer_id:
            child.set("style", "display:none")
    import xml.etree.ElementTree as ET
    return ET.tostring(root, encoding="unicode")


@unittest.skipUnless(drawing.INKSCAPE and drawing.pillow(), "needs inkscape and Pillow")
class RenderTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.renders = {project: drawing.render(drawing.document(project), DPI)
                       for project in drawing.projects()}

    def each(self):
        self.assertTrue(self.renders, "no projects")
        for project, image in self.renders.items():
            yield project, image

    def test_size(self):
        for project, image in self.each():
            with self.subTest(project=project):
                root = drawing.parse(drawing.document(project))
                width, height = (float(re.sub("px$", "", root.get(k))) for k in ("width", "height"))
                expected = (round(width * DPI / 96), round(height * DPI / 96))
                for got, want in zip(image.size, expected):
                    self.assertLessEqual(abs(got - want), 1, f"rendered {image.size}, expected {expected}")

    def test_covers_the_page(self):
        for project, image in self.each():
            with self.subTest(project=project):
                alpha = image.getchannel("A")
                transparent = alpha.histogram()[0] / (image.width * image.height)
                self.assertLessEqual(transparent, TRANSPARENT_MAX,
                                     f"{transparent:.1%} of the page is transparent")

    def test_is_exposed_and_has_contrast(self):
        for project, image in self.each():
            with self.subTest(project=project):
                stat = luminance(image)
                self.assertGreater(stat.mean[0], DARK, "the picture is black")
                self.assertLess(stat.mean[0], BRIGHT, "the picture is washed out")
                self.assertGreater(stat.stddev[0], CONTRAST_MIN, "the picture is flat")

    def test_every_layer_shows(self):
        # a layer that changes nothing is hidden, covered or off the page
        for project, image in self.each():
            with self.subTest(project=project):
                text = drawing.document(project)
                for child in drawing.parse(text):
                    label = child.get(f"{{{drawing.INKSCAPE_NS}}}label")
                    if not label:
                        continue
                    hidden = drawing.render(without_layer(text, child.get("id")), DPI)
                    share = changed(image, hidden)
                    self.assertGreater(share, LAYER_MIN,
                                       f"hiding the layer {label} changes {share:.2%} of the picture")

    def test_the_gallery_is_up_to_date(self):
        for project, image in self.each():
            with self.subTest(project=project):
                for path in sorted((drawing.ROOT / "gallery").glob(f"{project}.*")):
                    if path.suffix == ".svg":
                        shown = drawing.render(path.read_text(), DPI)
                    else:
                        from PIL import Image
                        with Image.open(path) as picture:
                            shown = picture.convert("RGBA").resize(image.size)
                    self.assertLess(difference(image, shown), GALLERY_MAX,
                                    f"{path.name} no longer matches the drawing")


if __name__ == "__main__":
    unittest.main()
