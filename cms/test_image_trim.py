"""Checks for the white-margin trim applied to uploaded images.

The team cards crop square, so a photo exported with padding baked into the
frame would show that padding as bars. `trim_uniform_border` removes it, but
it has to tell deliberate padding apart from a portrait shot on a white
studio backdrop — cropping the latter would zoom into the subject and knock
them off centre.

Run with:  python3 test_image_trim.py
"""

import os
import sys

from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import trim_uniform_border  # noqa: E402

PHOTOS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Emma-Basic-The-Basic-Ingredients", "project", "assets", "Employees-page",
)

WHITE = (255, 255, 255)


def photo(name, box=1200):
    img = ImageOps.exif_transpose(Image.open(os.path.join(PHOTOS, name)))
    img = img.convert("RGB")
    img.thumbnail((box, box))
    return img


def pad(img, left, top, right, bottom):
    out = Image.new("RGB", (img.width + left + right, img.height + top + bottom), WHITE)
    out.paste(img, (left, top))
    return out


def expect(label, img, should_trim, failures):
    before = img.size
    after = trim_uniform_border(img).size
    trimmed = after != before
    ok = trimmed == should_trim
    if not ok:
        failures.append(label)
    print("%-9s %-46s %dx%d -> %dx%d" % (
        "ok" if ok else "FAILED", label, before[0], before[1], after[0], after[1]))


def main():
    failures = []

    # Padding the trim is meant to remove.
    square = photo("itsuro 1.jpg", 900)
    expect("even frame on all four edges", pad(square, 120, 120, 120, 120), True, failures)

    landscape = photo("cotton 2.jpg", 1000)
    bars = (landscape.width - landscape.height) // 2
    expect("landscape letterboxed to square", pad(landscape, 0, bars, 0, bars), True, failures)

    portrait = photo("James 1.jpg", 900)
    sides = (portrait.height - portrait.width) // 2
    expect("portrait pillarboxed to square", pad(portrait, sides, 0, sides, 0), True, failures)

    # A frame may use different amounts horizontally and vertically and is
    # still deliberate, so long as each opposite pair matches.
    expect("thin sides, deep top and bottom", pad(square, 20, 160, 20, 160), True, failures)

    # A lone bright edge is part of the photograph, not padding.
    one_edge = Image.new("RGB", (800, 800), (120, 120, 120))
    one_edge.paste(Image.new("RGB", (800, 120), WHITE), (0, 0))
    expect("single white edge", one_edge, False, failures)

    # Lopsided within a pair means it was not applied as a frame.
    expect("top and bottom margins unequal",
           pad(landscape, 0, 40, 0, 160), False, failures)

    # Real photographs must survive untouched — "ran 1.jpg" is the important
    # one here, a portrait on a white studio backdrop.
    for name in ("ran 1.jpg", "James 1.jpg", "itsuro 1.jpg", "olivia.jpg",
                 "taiki.jpg", "cotton 1.jpg", "Nancy 1.jpg", "ling 1.jpg",
                 "emma 1.jpg", "emma 2.jpg", "ling 2.jpg", "yoko.png"):
        expect("untouched: %s" % name, photo(name), False, failures)

    print()
    if failures:
        print("%d failed: %s" % (len(failures), ", ".join(failures)))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
