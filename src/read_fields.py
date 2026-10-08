"""Read the Jackery Explorer 300 Plus display fields from Pi camera photos with Tesseract.

Usage: python3 read_fields.py photo.jpg [photo.jpg ...] > readings.csv

Photos must be taken as in the 2026-10-07 bench run: v2.1 camera ~10 cm from the display,
lens turned ~90 deg counterclockwise, dark room,
  rpicam-still --rotation 180 --shutter 50000 --gain 4 --awbgains 1.5,1.5
Boxes are in full-frame pixels (3280 x 2464) for that mounting, and are shifted and scaled
to follow the display in each photo (see REFERENCE_OUTLINE). A tilt or rotation of the
camera is not followed.
"""
import collections, csv, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageChops, ImageFilter, ImageOps

TESSDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tessdata")

# name: (box, green threshold). Boxes are sized for the widest value each field can show,
# not the one on screen.
# Threshold is on the GREEN channel: the lit segments' cores are near-white and their glow
# is pure blue, so green picks out solid segments without the halo (thresholding on "more
# blue than red or green" keeps only the glow and gives hollow outlines). The small time
# fields are much dimmer than the rest -- the lens is less sharp out there -- so they need a
# lower threshold.
FIELDS = {
    "soc":           ((1360,  955, 1610, 1135), 120),  # % left out; room for a leading 1
    "input_watts":   (( 980,  955, 1235, 1070), 120),  # 3 digits + W
    "time_to_full":  ((1000, 1070, 1230, 1160),  45),  # shown only while charging
    "output_watts":  ((1760, 1005, 2085, 1105), 120),  # right-aligned; room for 3 digits + W
    "time_to_empty": ((1840, 1110, 2085, 1205),  45),  # shows 99.9H while charging
}

# Outline of the lit blue parts of the display (Wi-Fi icon to time-to-empty) in the photos
# the boxes above were measured on. Each photo's own outline is found and the boxes are
# shifted and scaled to match, so they follow the display when the camera moves or changes
# distance. The orange ring and the green LED are not blue, so they don't count.
REFERENCE_OUTLINE = (947, 687, 2091, 1195)


def outline(im):
    r, g, b = im.convert("RGB").split()
    # MinFilter(5) drops specks under 5 px across -- single stray blue pixels elsewhere in
    # the frame threw the outline off in 3 of the 180 photos of 2026-10-07.
    return ImageChops.subtract(b, ImageChops.lighter(r, g)).point(
        lambda p: 255 if p > 40 else 0).filter(ImageFilter.MinFilter(5)).getbbox()


def place(box, found):
    """Move a box measured against REFERENCE_OUTLINE onto this photo's outline."""
    rx, ry = REFERENCE_OUTLINE[:2]
    k = (found[2] - found[0]) / (REFERENCE_OUTLINE[2] - REFERENCE_OUTLINE[0])
    return tuple(round(v) for v in (found[0] + (box[0] - rx) * k, found[1] + (box[1] - ry) * k,
                                    found[0] + (box[2] - rx) * k, found[1] + (box[3] - ry) * k))


# Letters the 7seg model returns for digits.
SWAPS = str.maketrans({"O": "0", "Q": "0", "D": "0", "G": "6", "I": "1", "l": "1",
                       "S": "5", "B": "8", "Z": "2", "Y": "4", "V": "4"})


def prepare(im, box, threshold, size=None):
    """Crop one field and make it black digits on white with a margin, for Tesseract.
    size: scale the crop to this (width, height) first, so digits are the same size in
    pixels whatever the camera distance (Tesseract failed on the larger digits at 7 cm)."""
    g = im.convert("RGB").split()[1].crop(box)
    if size:
        g = g.resize(size, Image.LANCZOS)
    # Thicken the segments by a pixel each way (jacktessery's dilate). Without it Tesseract
    # read nothing at 7 cm, where the gaps between segments are sharp.
    bw = ImageOps.invert(g.point(lambda p: 255 if p > threshold else 0)).filter(ImageFilter.MinFilter(3))
    return ImageOps.expand(bw, 20, fill=255)


def clean(raw):
    """Keep the leading number; ignore whatever the unit letter was read as (H, M, H4, 4...).
    Returns '' for a blank field, '?raw' for an unreadable one."""
    m = re.match(r"\d+(\.\d)?", raw.replace(" ", "").translate(SWAPS))
    return m.group(0) if m else ("" if not raw else "?" + raw)


def ocr(im, name, found):
    box, threshold = FIELDS[name]
    with tempfile.NamedTemporaryFile(suffix=".png") as t:
        prepare(im, place(box, found), threshold, (box[2] - box[0], box[3] - box[1])).save(t.name)
        return subprocess.run(["tesseract", t.name, "-", "--tessdata-dir", TESSDATA,
                               "-l", "7seg", "--psm", "7"],
                              capture_output=True, text=True).stdout.strip()


def read_photo(path):
    im = Image.open(path)
    im.load()
    found = outline(im)
    if found is None:
        return {name: "dark" for name in FIELDS}
    return {name: clean(ocr(im, name, found)) for name in FIELDS}


def vote(readings, n):
    """Majority of the last n readings of one field, or None if no value has a majority.
    On the 2026-10-07 run it cut time-to-empty misreads from 19 to about 6 of 180; it does
    not remove them, because misreads cluster."""
    window = readings[-n:]
    value, count = collections.Counter(window).most_common(1)[0]
    return value if count * 2 > len(window) else None


if __name__ == "__main__":
    paths = sorted(sys.argv[1:])
    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(read_photo, paths))
    w = csv.writer(sys.stdout)
    w.writerow(["photo"] + list(FIELDS))
    for path, r in zip(paths, results):
        w.writerow([os.path.basename(path)] + [r[n] for n in FIELDS])
