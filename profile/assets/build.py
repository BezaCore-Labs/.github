"""Build the profile's images from BezaCore Labs' own brand sources.

Everything with words in it is outlines, not live text: GitHub shows an SVG in
an `<img>`, where web fonts never load, so live text would fall back to
whatever the reader has installed. Every colour is a brand token, or a mix of
two tokens the way bezacore.com mixes them. The logo is the master file,
embedded whole and unchanged.

Run by hand when an image changes, not by any build. Needs `fontTools`:

    python profile/assets/build.py --brand <bezacore-labs>/brand

`--brand` is the brand directory of the BezaCore Labs hub repository, which
supplies the fonts (`fonts/`, SIL Open Font License 1.1) and the logo masters
(`masters/`). `--still` builds every image without motion.

The four icons are Lucide's (ISC licence), the family bezacore.com uses.
"""

from __future__ import annotations

import argparse
import math
import pathlib
import re
import shutil

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

HERE = pathlib.Path(__file__).parent

# Brand tokens (bezacore-labs/brand/tokens), dark and light.
PAGE = "#081221"
PAPER = "#F2F7FE"
INK = {"dark": "#EEF2F7", "light": "#181928"}
MID = {"dark": "#B6BFCB", "light": "#5C646F"}  # neutral 300 on dark, muted-foreground on light
ACCENT = "#F7D710"
BRAND = "#483BBA"
INDIGO_400 = "#8C91FB"


def _oklab(hex_colour: str) -> tuple[float, float, float]:
    def linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(int(hex_colour[i : i + 2], 16) / 255) for i in (1, 3, 5))
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def _hex(lab: tuple[float, float, float]) -> str:
    L, a, b = lab
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )

    def gamma(c: float) -> int:
        c = min(max(c, 0.0), 1.0)
        c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
        return round(c * 255)

    return "#" + "".join(f"{gamma(c):02X}" for c in rgb)


def mix(first: str, share: float, second: str) -> str:
    """CSS `color-mix(in oklab, first share, second)`."""
    a, b = _oklab(first), _oklab(second)
    return _hex(tuple(share * x + (1 - share) * y for x, y in zip(a, b, strict=True)))  # type: ignore[arg-type]


# A section's colour: where a heading's phrase starts, and where it deepens to.
# Dark values are bezacore.com's (`--site-*` and `--site-*-deep`); light values
# are the same hues two or three steps deeper, so they pass on white.
TONES = {
    "cyan": {"dark": ("#83DCFE", "#0CAEDB"), "light": ("#017A9B", "#01617D")},
    "lilac": {"dark": ("#B0B7FF", INDIGO_400), "light": (BRAND, "#33278C")},
    "orange": {
        "dark": (mix("#EB7007", 0.55, "#F5AA80"), mix("#EB7007", 0.60, "#F7A224")),
        "light": ("#A44C03", "#8B3F01"),
    },
    "amber": {"dark": ("#F7A224", mix("#D98B09", 0.50, "#F7A224")), "light": ("#915B02", "#7B4C02")},
}
RING_QUIET = {"dark": (INDIGO_400, 0.34), "light": (BRAND, 0.22)}

# Lucide 1.48.0, ISC licence, Copyright (c) Lucide Contributors.
ICONS = {
    "receipt-text": [
        ("path", {"d": "M13 16H8"}),
        ("path", {"d": "M14 8H8"}),
        ("path", {"d": "M16 12H8"}),
        (
            "path",
            {
                "d": "M4 3a1 1 0 0 1 1-1 1.3 1.3 0 0 1 .7.2l.933.6a1.3 1.3 0 0 0 1.4 0l.934-.6a1.3 1.3 0 0 1 1.4 0l.933.6"
                "a1.3 1.3 0 0 0 1.4 0l.933-.6a1.3 1.3 0 0 1 1.4 0l.934.6a1.3 1.3 0 0 0 1.4 0l.933-.6A1.3 1.3 0 0 1 19 2"
                "a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1 1.3 1.3 0 0 1-.7-.2l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.934.6a1.3 1.3 0 0 1-1.4 0"
                "l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.933.6a1.3 1.3 0 0 1-1.4 0l-.934-.6a1.3 1.3 0 0 0-1.4 0l-.933.6"
                "a1.3 1.3 0 0 1-.7.2 1 1 0 0 1-1-1z"
            },
        ),
    ],
    "key-round": [
        (
            "path",
            {
                "d": "M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1"
                "a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"
            },
        ),
        ("circle", {"cx": "16.5", "cy": "7.5", "r": ".5", "fill": "currentColor"}),
    ],
    "message-square-text": [
        (
            "path",
            {
                "d": "M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5"
                "a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"
            },
        ),
        ("path", {"d": "M7 11h10"}),
        ("path", {"d": "M7 15h6"}),
        ("path", {"d": "M7 7h8"}),
    ],
    "circle-dot": [
        ("circle", {"cx": "12", "cy": "12", "r": "1"}),
        ("circle", {"cx": "12", "cy": "12", "r": "10"}),
    ],
}


def _number(value: float) -> str:
    """Path coordinates to a tenth of a pixel, which is finer than any screen draws."""
    text = f"{value:.1f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


class Type:
    """A font instance that sets a line of text as outlines, kerned by its own GPOS table."""

    def __init__(self, path: pathlib.Path, **axes: float) -> None:
        self.font = instantiateVariableFont(TTFont(path), axes, inplace=True) if axes else TTFont(path)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upem = self.font["head"].unitsPerEm
        self.pairs: dict[tuple[str, str], int] = {}
        self.classes: list = []
        if "GPOS" in self.font:
            for lookup in self.font["GPOS"].table.LookupList.Lookup:
                subtables = lookup.SubTable
                if lookup.LookupType == 9:
                    subtables = [extension.ExtSubTable for extension in subtables]
                for sub in subtables:
                    if getattr(sub, "LookupType", 2) != 2:
                        continue
                    if sub.Format == 1:
                        for first, pairset in zip(sub.Coverage.glyphs, sub.PairSet, strict=False):
                            for record in pairset.PairValueRecord:
                                value = getattr(record.Value1, "XAdvance", 0) or 0
                                if value:
                                    self.pairs.setdefault((first, record.SecondGlyph), value)
                    elif sub.Format == 2:
                        self.classes.append(sub)

    def _kern(self, left: str, right: str) -> int:
        if (left, right) in self.pairs:
            return self.pairs[(left, right)]
        for sub in self.classes:
            if left not in sub.Coverage.glyphs:
                continue
            first = sub.ClassDef1.classDefs.get(left, 0)
            second = sub.ClassDef2.classDefs.get(right, 0)
            value = getattr(sub.Class1Record[first].Class2Record[second].Value1, "XAdvance", 0) or 0
            if value:
                return int(value)
        return 0

    def _layout(self, text: str, tracking: float) -> list[tuple[str, float]]:
        names = [self.cmap[ord(character)] for character in text]
        placed, advance = [], 0.0
        for index, name in enumerate(names):
            placed.append((name, advance))
            advance += self.glyphs[name].width + tracking * self.upem / 1000
            if index + 1 < len(names):
                advance += self._kern(name, names[index + 1])
        placed.append(("", advance))
        return placed

    def width(self, text: str, size: float, tracking: float = 0) -> float:
        return self._layout(text, tracking)[-1][1] * size / self.upem

    def paths(self, text: str, *, x: float, baseline: float, size: float, tracking: float = 0) -> list[tuple[str, float]]:
        """One path's `d` per character, in pixel space, with each character's left edge."""
        scale = size / self.upem
        out = []
        for name, advance in self._layout(text, tracking)[:-1]:
            pen = SVGPathPen(self.glyphs, ntos=_number)
            left = x + advance * scale
            self.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, left, baseline)))
            out.append((pen.getCommands(), left))
        return out

    def text(self, text: str, *, x: float, baseline: float, size: float, fill: str, tracking: float = 0) -> str:
        d = "".join(d for d, _ in self.paths(text, x=x, baseline=baseline, size=size, tracking=tracking))
        return f'<path fill="{fill}" d="{d}"/>' if d else ""


class Fonts:
    def __init__(self, brand: pathlib.Path) -> None:
        fonts = brand / "fonts"
        self.archivo = Type(fonts / "archivo" / "archivo.ttf", wght=600, wdth=100)
        self.inter = Type(fonts / "inter" / "inter_roman.ttf", wght=400, opsz=20)
        self.inter_medium = Type(fonts / "inter" / "inter_roman.ttf", wght=500, opsz=14)


def svg(width: float, height: float, body: str, label: str | None, style: str = "") -> str:
    a11y = f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
    css = f"<style>{style}</style>" if style else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" {a11y}>{css}{body}</svg>\n'
    )


def master(brand: pathlib.Path, name: str, *, x: float, y: float, width: float) -> str:
    """A logo master, whole and unchanged, placed by nesting it with its own viewBox."""
    source = (brand / "masters" / f"{name}.svg").read_text()
    box = re.search(r'viewBox="([^"]+)"', source)
    assert box is not None
    _, _, w, h = (float(v) for v in box[1].split())
    inner = source[source.index(">") + 1 : source.rindex("</svg>")]
    return (
        f'<svg x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{width * h / w:.1f}" '
        f'viewBox="{box[1]}">{inner}</svg>'
    )


# Motion, after bezacore.com's rings: each ring draws in once from the top, in
# turn from the core outward, and the core grows into place; then nothing moves.
# Eased with no overshoot. Nothing runs for a reader who asks for reduced motion.
MOTION = """
@media (prefers-reduced-motion: no-preference) {
  .ring { stroke-dasharray: 1; animation: draw 1.4s cubic-bezier(0.42, 0, 0.58, 1) both; }
  .r2 { animation-delay: 0.12s; } .r3 { animation-delay: 0.24s; }
  .r4 { animation-delay: 0.36s; } .r5 { animation-delay: 0.48s; }
  .core { transform-box: fill-box; transform-origin: 50% 50%;
          animation: grow 0.6s cubic-bezier(0.3, 0.6, 0.2, 1) 0.1s both; }
}
@keyframes draw { from { stroke-dashoffset: 1; } }
@keyframes grow { from { transform: scale(0); } }
"""


def rings(cx: float, cy: float, scale: float, mode: str, *, stroke: float = 1.5, core: bool = True) -> str:
    """The mark's geometry, drawn large: bezacore.com's five rings around the yellow core."""
    quiet, quiet_alpha = RING_QUIET[mode]
    cyan, lilac = TONES["cyan"][mode][0], TONES["lilac"][mode][0]
    spec = [
        (110, cyan, 0.85),
        (190, lilac, 0.55),
        (275, quiet, quiet_alpha),
        (365, quiet, quiet_alpha),
        (460, quiet, quiet_alpha * 0.55),
    ]
    out = []
    for index, (radius, colour, alpha) in enumerate(spec, start=1):
        out.append(
            f'<circle class="ring r{index}" cx="{cx:.1f}" cy="{cy:.1f}" r="{radius * scale:.1f}" pathLength="1" '
            f'fill="none" stroke="{colour}" stroke-opacity="{alpha}" stroke-width="{stroke}" '
            f'transform="rotate(-90 {cx:.1f} {cy:.1f})"/>'
        )
    if core:
        out.append(f'<circle class="core" cx="{cx:.1f}" cy="{cy:.1f}" r="{22 * scale:.1f}" fill="{ACCENT}"/>')
    return "".join(out)


def dot(x: float, baseline: float, size: float, mode: str, ident: str) -> tuple[str, str]:
    """The yellow full stop after a heading, with the core's soft halo on dark."""
    r = size * 0.085
    cy = baseline - r
    if mode == "light":
        return "", f'<circle cx="{x + r:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{BRAND}"/>'
    blur = min(size * 0.14, 14) / 2.5
    defs = (
        f'<filter id="{ident}" x="-200%" y="-200%" width="500%" height="500%">'
        f'<feGaussianBlur stdDeviation="{blur:.2f}"/></filter>'
    )
    body = (
        f'<circle cx="{x + r:.1f}" cy="{cy:.1f}" r="{r * 1.3:.1f}" fill="{ACCENT}" opacity="0.55" filter="url(#{ident})"/>'
        f'<circle cx="{x + r:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{ACCENT}"/>'
    )
    return defs, body


def heading_line(
    fonts: Fonts, before: str, phrase: str, after: str, *, x: float, baseline: float, size: float, tone: str, mode: str, ident: str
) -> tuple[str, str, float]:
    """A heading whose phrase fades across its length in the section's colour, ending on the dot.

    Returns the definitions, the body and the width the line takes.
    """
    face, tracking = fonts.archivo, -10
    start, deep = TONES[tone][mode]
    defs, body = [], []
    cursor = x
    if before:
        body.append(face.text(before, x=cursor, baseline=baseline, size=size, fill=INK[mode], tracking=tracking))
        cursor += face.width(before, size, tracking)
    phrase_width = face.width(phrase, size, tracking)
    defs.append(
        f'<linearGradient id="{ident}-fade" gradientUnits="userSpaceOnUse" x1="{cursor:.1f}" y1="0" '
        f'x2="{cursor + phrase_width:.1f}" y2="0"><stop offset="0" stop-color="{start}"/>'
        f'<stop offset="1" stop-color="{deep}"/></linearGradient>'
    )
    body.append(face.text(phrase, x=cursor, baseline=baseline, size=size, fill=f"url(#{ident}-fade)", tracking=tracking))
    cursor += phrase_width
    if after:
        body.append(face.text(after, x=cursor, baseline=baseline, size=size, fill=INK[mode], tracking=tracking))
        cursor += face.width(after, size, tracking)
    dot_defs, dot_body = dot(cursor + size * 0.06, baseline, size, mode, f"{ident}-glow")
    defs.append(dot_defs)
    body.append(dot_body)
    return "".join(defs), "".join(body), cursor + size * 0.06 + size * 0.17 - x


def label(fonts: Fonts, text: str, *, x: float, baseline: float, size: float, tone: str, mode: str) -> tuple[str, float]:
    """A section's small label, in its colour, after a ring of the mark's geometry."""
    colour = TONES[tone][mode][0] if mode == "dark" else TONES[tone][mode][1]
    r = size * 0.36
    ring = (
        f'<circle cx="{x + r:.1f}" cy="{baseline - size * 0.36:.1f}" r="{r:.1f}" fill="none" '
        f'stroke="{colour}" stroke-width="1.5"/>'
    )
    left = x + 2 * r + size * 0.6
    words = fonts.inter_medium.text(text, x=left, baseline=baseline, size=size, fill=colour, tracking=10)
    return ring + words, left - x + fonts.inter_medium.width(text, size, 10)


def section(fonts: Fonts, name: str, tag: str, before: str, phrase: str, after: str, tone: str, mode: str) -> str:
    size, label_size = 34, 15
    pad = 4
    label_body, _ = label(fonts, tag, x=pad, baseline=22, size=label_size, tone=tone, mode=mode)
    defs, body, width = heading_line(
        fonts, before, phrase, after, x=pad, baseline=74, size=size, tone=tone, mode=mode, ident=f"{name}-{mode}"
    )
    text = f"{before}{phrase}{after}"
    return svg(width + 2 * pad + 12, 90, f"<defs>{defs}</defs>{label_body}{body}", text)


def banner(fonts: Fonts, brand: pathlib.Path, still: bool) -> str:
    width, height = 1280, 440
    mode = "dark"
    parts = [
        f'<rect width="{width}" height="{height}" rx="20" fill="{PAGE}"/>',
        '<clipPath id="card"><rect width="1280" height="440" rx="20"/></clipPath>',
        f'<g clip-path="url(#card)">{rings(1060, 220, 0.44, mode, stroke=1.6)}</g>',
        master(brand, "bezacore_horizontal_on-dark", x=64, y=44, width=340),
    ]
    tag, _ = label(fonts, "A software studio", x=96, baseline=196, size=17, tone="lilac", mode=mode)
    parts.append(tag)
    size = 58
    first = fonts.archivo.text(
        "Purposeful software for", x=94, baseline=270, size=size, fill=INK[mode], tracking=-20
    )
    defs, second, _ = heading_line(
        fonts, "", "meaningful work", "", x=94, baseline=338, size=size, tone="cyan", mode=mode, ident="banner"
    )
    parts += [first, second]
    parts.append(
        fonts.inter.text(
            "Software built for the work small teams actually do.", x=96, baseline=392, size=22, fill=MID[mode]
        )
    )
    label_text = "BezaCore Labs. A software studio. Purposeful software for meaningful work."
    return svg(width, height, f"<defs>{defs}</defs>" + "".join(parts), label_text, "" if still else MOTION)


def building(mode: str, still: bool) -> str:
    """A ring partly drawn around the core: software still being built."""
    size = 160
    c = size / 2
    lilac = TONES["lilac"][mode][0]
    quiet, quiet_alpha = RING_QUIET[mode]
    r_in, r_out = 34, 64
    body = (
        f'<circle cx="{c}" cy="{c}" r="{r_out}" fill="none" stroke="{quiet}" stroke-opacity="{quiet_alpha}" '
        f'stroke-width="1.5" stroke-dasharray="2 7" stroke-linecap="round"/>'
        f'<circle class="ring r2" cx="{c}" cy="{c}" r="{r_out}" pathLength="1" fill="none" stroke="{lilac}" '
        f'stroke-width="2.5" stroke-linecap="round" stroke-dasharray="0.62 1" transform="rotate(-90 {c} {c})"/>'
        f'<circle class="ring r1" cx="{c}" cy="{c}" r="{r_in}" pathLength="1" fill="none" '
        f'stroke="{TONES["cyan"][mode][0]}" stroke-opacity="0.85" stroke-width="1.5" transform="rotate(-90 {c} {c})"/>'
        f'<circle class="core" cx="{c}" cy="{c}" r="9" fill="{ACCENT}"/>'
    )
    # The partly drawn ring keeps its gap: it draws to 62%, not to a whole circle.
    style = "" if still else MOTION.replace("stroke-dasharray: 1;", "") + (
        ".r2 { stroke-dasharray: 0.62 1; animation-name: draw-part; }"
        "@keyframes draw-part { from { stroke-dasharray: 0 1; } }"
        ".r1 { stroke-dasharray: 1; }"
    )
    return svg(size, size, body, None, style)


def icon(name: str, tone: str, mode: str) -> str:
    colour = TONES[tone][mode][0] if mode == "dark" else TONES[tone][mode][1]
    shapes = []
    for tag, attributes in ICONS[name]:
        extra = " ".join(f'{key}="{colour if value == "currentColor" else value}"' for key, value in attributes.items())
        shapes.append(f"<{tag} {extra}/>")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="-2 -2 28 28" aria-hidden="true">'
        "<!-- Lucide, ISC licence, Copyright (c) Lucide Contributors -->"
        f'<g fill="none" stroke="{colour}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        + "".join(shapes)
        + "</g></svg>\n"
    )


SECTIONS = [
    # file name, label, before, phrase, after, tone
    ("lab", "In the lab", "Open source, ", "in daily use", "", "cyan"),
    ("next", "Software", "What we’re ", "building next", "", "amber"),
    ("how", "How we work", "Straight with you, ", "start to finish", "", "lilac"),
    ("work", "Work with us", "Tell us what you’re ", "working on", "", "orange"),
    ("tools", "Tools", "What we ", "build with", "", "cyan"),
]

WAYS = [("receipt-text", "cyan"), ("key-round", "orange"), ("message-square-text", "amber"), ("circle-dot", "lilac")]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brand", type=pathlib.Path, required=True)
    parser.add_argument("--still", action="store_true", help="build every image without motion")
    arguments = parser.parse_args()
    brand: pathlib.Path = arguments.brand
    fonts = Fonts(brand)

    written = {"banner.svg": banner(fonts, brand, arguments.still)}
    for mode in ("dark", "light"):
        for name, tag, before, phrase, after, tone in SECTIONS:
            written[f"heading_{name}_{mode}.svg"] = section(fonts, name, tag, before, phrase, after, tone, mode)
        written[f"building_{mode}.svg"] = building(mode, arguments.still)
        for icon_name, tone in WAYS:
            written[f"icon_{icon_name}_{mode}.svg"] = icon(icon_name, tone, mode)
    for name, content in written.items():
        (HERE / name).write_text(content)
    for variant in ("on-dark", "full-colour"):
        shutil.copyfile(brand / "masters" / f"bezacore_mark_{variant}.svg", HERE / f"bezacore_mark_{variant}.svg")
    print(f"wrote {len(written) + 2} files to {HERE}")


if __name__ == "__main__":
    main()
