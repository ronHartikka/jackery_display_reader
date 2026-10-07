"""Read the Jackery Explorer 300 Plus display fields from Pi camera photos with Tesseract.

Usage: python3 read_fields.py photo.jpg [photo.jpg ...] > readings.csv

Photos must be taken as in the 2026-10-07 bench run: v2.1 camera ~10 cm from the display,
lens turned ~90 deg counterclockwise, dark room,
  rpicam-still --rotation 180 --shutter 50000 --gain 4 --awbgains 1.5,1.5
Boxes are in full-frame pixels (3280 x 2464) for that mounting. If the camera moves, they
must be found again.
"""
import collections, csv, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

TESSDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tessdata")

# name: (box, green threshold). Boxes are sized for the widest value each field can show,
# not the one on screen.
# Threshold is on the GREEN channel: the lit segments' cores are near-white and their glow
# is pure blue, so green picks out solid segments without the halo (thresholding on "more
# blue than red or green" keeps only the glow and gives hollow outlines). The small time
# fields are much dimmer than the rest -- the lens is less sharp out there -- so they need a
# lower threshold.
FIELDS = {
    "soc":           ((1360,  955, 1600, 1135), 120),  # % left out; room for a leading 1
    "input_watts":   (( 980,  955, 1235, 1070), 120),  # 3 digits + W
    "time_to_full":  ((1000, 1070, 1230, 1160),  45),  # shown only while charging
    "output_watts":  ((1760, 1005, 2085, 1105), 120),  # right-aligned; room for 3 digits + W
    "time_to_empty": ((1840, 1110, 2085, 1205),  45),  # shows 99.9H while charging
}

# Letters the 7seg model returns for digits.
SWAPS = str.maketrans({"O": "0", "Q": "0", "D": "0", "G": "6", "I": "1", "l": "1",
                       "S": "5", "B": "8", "Z": "2", "Y": "4"})


def prepare(im, box, threshold):
    """Crop one field and make it black digits on white with a margin, for Tesseract."""
    g = im.convert("RGB").split()[1].crop(box)
    return ImageOps.expand(ImageOps.invert(g.point(lambda p: 255 if p > threshold else 0)),
                           20, fill=255)


def clean(raw):
    """Keep the leading number; ignore whatever the unit letter was read as (H, M, H4, 4...).
    Returns '' for a blank field, '?raw' for an unreadable one."""
    m = re.match(r"\d+(\.\d)?", raw.replace(" ", "").translate(SWAPS))
    return m.group(0) if m else ("" if not raw else "?" + raw)


def ocr(im, name):
    with tempfile.NamedTemporaryFile(suffix=".png") as t:
        prepare(im, *FIELDS[name]).save(t.name)
        return subprocess.run(["tesseract", t.name, "-", "--tessdata-dir", TESSDATA,
                               "-l", "7seg", "--psm", "7"],
                              capture_output=True, text=True).stdout.strip()


def read_photo(path):
    im = Image.open(path)
    im.load()
    return {name: clean(ocr(im, name)) for name in FIELDS}


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
