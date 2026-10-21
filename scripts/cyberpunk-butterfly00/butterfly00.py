import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
INKSCAPE = "http://www.inkscape.org/namespaces/inkscape"
XLINK = "http://www.w3.org/1999/xlink"

WIDTH = 1920
HEIGHT = 1080
HORIZON = 680
CENTER_X = WIDTH // 2
CENTER_Y = 430

ET.register_namespace("", SVG)
ET.register_namespace("inkscape", INKSCAPE)
ET.register_namespace("xlink", XLINK)


def new_document(width, height):
    svg = ET.Element(f"{{{SVG}}}svg", width=str(width), height=str(height),
                     viewBox=f"0 0 {width} {height}")
    ET.SubElement(svg, f"{{{SVG}}}defs", id="defs")
    return svg


def element(parent, tag, **attributes):
    """Attribute names use "_" for "-", e.g. stroke_width="2"."""
    return ET.SubElement(parent, f"{{{SVG}}}{tag}",
                         {key.replace("_", "-"): str(value)
                          for key, value in attributes.items()})


def defs(svg):
    return svg.find(f"{{{SVG}}}defs")


def add_layer(svg, name, opacity=1.0):
    layer = element(svg, "g", id=name.lower().replace(" ", "-"),
                    opacity=opacity)
    layer.set(f"{{{INKSCAPE}}}groupmode", "layer")
    layer.set(f"{{{INKSCAPE}}}label", name)
    return layer


def linear_gradient(svg, gradient_id, stops, start, end):
    return gradient(svg, "linearGradient", gradient_id, stops,
                    gradientUnits="userSpaceOnUse",
                    x1=start[0], y1=start[1], x2=end[0], y2=end[1])


def radial_gradient(svg, gradient_id, stops, center=None, radius=None):
    """Without center and radius the gradient spans each filled shape."""
    if center is None:
        return gradient(svg, "radialGradient", gradient_id, stops,
                        cx=0.5, cy=0.5, r=0.5)
    return gradient(svg, "radialGradient", gradient_id, stops,
                    gradientUnits="userSpaceOnUse",
                    cx=center[0], cy=center[1], r=radius)


def gradient(svg, tag, gradient_id, stops, **position):
    """Keep the stops in a gradient of their own, linked from the positioned
    one, like Inkscape does (the HTML5 canvas exporter relies on it)."""
    colors = element(defs(svg), "linearGradient", id=gradient_id + "-stops")
    for index, color in enumerate(stops):
        element(colors, "stop", offset=index / (len(stops) - 1),
                style=f"stop-color:{color}")
    positioned = element(defs(svg), tag, id=gradient_id, **position)
    positioned.set(f"{{{XLINK}}}href", f"#{gradient_id}-stops")
    return f"url(#{gradient_id})"


def glow_filter(svg, filter_id, radius):
    """Blur a copy of the element and lay the sharp original over it."""
    glow = element(defs(svg), "filter", id=filter_id, x="-50%", y="-50%",
                   width="200%", height="200%")
    element(glow, "feGaussianBlur", stdDeviation=radius, result="blur")
    merge = element(glow, "feMerge")
    element(merge, "feMergeNode", **{"in": "blur"})
    element(merge, "feMergeNode", **{"in": "SourceGraphic"})
    return f"url(#{filter_id})"


def path_data(strokes, closed=True):
    """Each stroke is a start point followed by cubic segments given as
    (control1, control2, end) point triples."""
    commands = []
    for start, *segments in strokes:
        commands.append("M %g,%g" % start)
        for segment in segments:
            commands.append("C " + " ".join("%g,%g" % point
                                            for point in segment))
        if closed:
            commands.append("Z")
    return " ".join(commands)


def mirror(points):
    return [(2 * CENTER_X - x, y) for x, y in points]


def mirror_stroke(stroke):
    start, *segments = stroke
    return [mirror([start])[0]] + [tuple(mirror(segment)) for segment in segments]


def add_sky(svg):
    sky = add_layer(svg, "Sky")
    element(sky, "rect", x=0, y=0, width=WIDTH, height=HORIZON,
            fill=linear_gradient(svg, "sky-gradient", ["#05010f", "#3b0a5c"],
                                 (0, 0), (0, HORIZON)))
    element(sky, "rect", x=0, y=HORIZON, width=WIDTH, height=HEIGHT - HORIZON,
            fill=linear_gradient(svg, "ground-gradient",
                                 ["#12002a", "#020008"],
                                 (0, HORIZON), (0, HEIGHT)))
    return sky


def add_sun(svg):
    sun = add_layer(svg, "Sun")
    radius = 300
    center_y = HORIZON - 60

    # visible bands between the stripes cut out of the lower half
    clip = element(defs(svg), "clipPath", id="sun-clip")
    top = center_y - radius
    for gap_top, gap in sorted((HORIZON - 40 - i * 34, 4 + 3 * i)
                               for i in range(7)):
        element(clip, "rect", x=0, y=top, width=WIDTH, height=gap_top - top)
        top = gap_top + gap
    element(clip, "rect", x=0, y=top, width=WIDTH, height=HORIZON - top)

    # SVG filters before clipping, so the glow goes on a group around it
    group = element(sun, "g", filter=glow_filter(svg, "sun-glow", 40))
    element(group, "circle", cx=CENTER_X, cy=center_y, r=radius,
            clip_path="url(#sun-clip)",
            fill=linear_gradient(svg, "sun-gradient", ["#ffd319", "#ff2975"],
                                 (0, HORIZON - 2 * radius), (0, HORIZON)))
    return sun


def add_grid(svg):
    grid = add_layer(svg, "Grid")
    lines = []
    for i in range(-14, 15):
        lines.append(f"M {CENTER_X + i * 40},{HORIZON} "
                     f"L {CENTER_X + i * 260},{HEIGHT}")
    depth = 6.0
    while depth < HEIGHT - HORIZON:
        y = HORIZON + depth
        lines.append(f"M 0,{y:g} L {WIDTH},{y:g}")
        depth *= 1.45

    element(element(defs(svg), "clipPath", id="grid-clip"), "rect",
            x=0, y=HORIZON, width=WIDTH, height=HEIGHT - HORIZON)
    element(grid, "path", d=" ".join(lines), fill="none", stroke="#ff00ff",
            stroke_width=2, clip_path="url(#grid-clip)",
            filter=glow_filter(svg, "grid-glow", 6))
    return grid


def wing_outlines():
    upper = [(CENTER_X - 12, CENTER_Y - 20),
             ((CENTER_X - 120, CENTER_Y - 260), (CENTER_X - 420, CENTER_Y - 330),
              (CENTER_X - 470, CENTER_Y - 230)),
             ((CENTER_X - 520, CENTER_Y - 120), (CENTER_X - 330, CENTER_Y + 20),
              (CENTER_X - 12, CENTER_Y + 10))]
    lower = [(CENTER_X - 12, CENTER_Y + 20),
             ((CENTER_X - 260, CENTER_Y + 30), (CENTER_X - 400, CENTER_Y + 170),
              (CENTER_X - 330, CENTER_Y + 260)),
             ((CENTER_X - 260, CENTER_Y + 340), (CENTER_X - 90, CENTER_Y + 230),
              (CENTER_X - 12, CENTER_Y + 60))]
    return [upper, lower]


def add_wings(svg):
    wings = add_layer(svg, "Wings", opacity=0.92)
    group = element(wings, "g", filter=glow_filter(svg, "wings-glow", 25))
    left = wing_outlines()
    outline = path_data(left + [mirror_stroke(stroke) for stroke in left])

    element(element(defs(svg), "clipPath", id="wings-clip"), "path",
            d=outline)
    element(group, "path", d=outline,
            fill=radial_gradient(svg, "wings-gradient", ["#00f0ff", "#7a00ff"],
                                 (CENTER_X, CENTER_Y), 480))

    spot = radial_gradient(svg, "spot-gradient", ["#ff2975", "#ffd319"])
    spots = element(group, "g", clip_path="url(#wings-clip)")
    for x, y, size in ((-330, -190, 90), (-200, -90, 60), (-250, 170, 70)):
        for cx in (CENTER_X + x, CENTER_X - x):
            element(spots, "circle", cx=cx, cy=CENTER_Y + y, r=size / 2,
                    fill=spot)

    element(group, "path", d=outline, fill="none", stroke="#e0ffff",
            stroke_width=5, stroke_linejoin="round")
    veins = [(start, (start, tip, tip)) for start, (_, _, tip), _ in left]
    veins = veins + [mirror_stroke(vein) for vein in veins]
    element(group, "path", d=path_data(veins, closed=False), fill="none",
            stroke="#e0ffff", stroke_width=2)
    return wings


def add_body(svg):
    body = add_layer(svg, "Body")
    group = element(body, "g", filter=glow_filter(svg, "body-glow", 12))
    element(group, "ellipse", cx=CENTER_X, cy=CENTER_Y + 40, rx=16, ry=130,
            fill=linear_gradient(svg, "body-gradient", ["#ffffff", "#ff2975"],
                                 (CENTER_X, CENTER_Y - 90),
                                 (CENTER_X, CENTER_Y + 170)))
    element(group, "circle", cx=CENTER_X, cy=CENTER_Y - 106, r=24,
            fill=radial_gradient(svg, "head-gradient", ["#ffffff", "#ff2975"],
                                 (CENTER_X, CENTER_Y - 110), 28))

    antenna = [(CENTER_X - 8, CENTER_Y - 125),
               ((CENTER_X - 30, CENTER_Y - 200), (CENTER_X - 90, CENTER_Y - 250),
                (CENTER_X - 130, CENTER_Y - 250))]
    element(group, "path",
            d=path_data([antenna, mirror_stroke(antenna)], closed=False),
            fill="none", stroke="#ff2975", stroke_width=4,
            stroke_linecap="round")
    return body


def butterfly00():
    svg = new_document(WIDTH, HEIGHT)
    add_sky(svg)
    add_sun(svg)
    add_grid(svg)
    add_wings(svg)
    add_body(svg)
    return ET.tostring(svg, encoding="unicode", xml_declaration=True)
