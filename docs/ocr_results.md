# OCR results

## 2026-10-07 — 180 frames from the 3-hour screen run

Photos: one a minute, 14:09 to 17:08, v2.1 camera ~10 cm from the display, settings as in
`src/read_fields.py`. Copies on the Pi in `~/run_2026_10_07/`. Readings from
`src/read_fields.py` (Tesseract `7seg`, `--psm 7`, green-channel threshold, letter-for-digit
fixes) are in `ocr_run_2026_10_07.csv`. No hand-checked value for each frame; correct values
come from the run hanging together (SOC 81% until 14:15, 80% as charging started, up 1% a
minute to 85% at 14:20; time-to-empty 45.5H at 81%, 99.9H while charging, 47.8H after) and
from looking at the crops behind every odd reading.

| field | right | wrong |
|---|---|---|
| SOC | 180 | 0 |
| input | 178 | 2 — leading 2 dropped (200 read 0, 207 read 7), both while charging |
| time to full | 180 | 0 (shown in 5 frames) |
| output | 179 | 1 blank (a failed read, not a wrong value) |
| time to empty | 161 | 19 — 47.8 read as 47.9 (18) or 47.0 (1) |

Every wrong value is a wrong digit on a small field, and it looks plausible. Most are the 8
in time-to-empty read as 9: its lower-left segment is faint, where the lens is least sharp.

Majority vote over the last 3 or 5 frames cuts time-to-empty from 19 wrong to about 6–7
(some of those are lag just after a real change). It does not remove them: misreads
cluster (47.9, 47.8, 47.9 gives 47.9 the majority). At one frame a minute, voting also
loses the majority while SOC is really changing 1%/minute during charging; at a few frames
a second it would not.

Time: 900 field reads in 7 s on the Mac (8 at a time). About 0.4 s per field on the Pi 3B.

Next, for the small fields: sharpen focus on that side of the display or move 2–3 mm, then
if needed check each segment's fixed pixel position for lit/unlit instead of Tesseract.

## 2026-10-08 — distance sweep, lens unchanged

Lens left as turned on 2026-10-07. Camera re-aimed slightly after Ron stabilised it.
Distance is lens face to display face. 5 frames at each distance, dark room; display
showing SOC 84%, input 0W, output 1W or 0W, time-to-empty 47.2H. Photos in
`captures/bench_2026_10_08/` (git-ignored), named by distance in mm.

| distance | frames with every field right | look of the small digits |
|---|---|---|
| 5 cm | 4 of 5 (one 47.2 read as 447.2) | softer, glow spreading |
| 6 cm | 5 of 5 | sharp |
| 7 cm | 5 of 5 | sharpest |
| 8 cm | 5 of 5 | slightly softer |
| 9 cm | 5 of 5 | softer |
| 10 cm (2026-10-07) | time-to-empty ~93% | blurry |

**The lens is focused near 7 cm.** That is why 10 cm was soft: 3 cm past focus.
Caveat: 5 frames each, and 47.2 contains no 8 — the digit that failed at 10 cm.

Room light ruins the small fields: with a basement light on, its reflection in the display
glass made time-to-empty and time-to-full unreadable at 5 and 8 cm (`d50_*`, `d80_*`;
reshot dark as `d50b_*`, `d80b_*`). The enclosure needs to keep light off the glass.

Script changes found by the sweep, each checked against the 180 frames of 2026-10-07:
- Boxes follow the display: each photo's outline is found and the boxes shifted and scaled.
- Each crop is scaled to its 10 cm size before OCR, so digit size does not change with
  distance.
- Segments thickened by a pixel each way before OCR. Without it Tesseract read nothing at
  7 cm, where the gaps between segments are sharp.
- Specks under 5 px are ignored when finding the outline (they threw it off in 3 frames).

With those, the 2026-10-07 frames score: SOC, input and output right in 180 of 180,
time-to-full wrong in 1, time-to-empty wrong in 13 (was 19).

## 2026-10-08 — run at 7 cm: idle, 80 W load, recharge

Camera 7 cm from the display (lens unchanged), room dark, basement window above the camera
covered. One photo a minute, 12:20 to 14:34, 135 photos in `captures/run_2026_10_08/`
(git-ignored); readings in `ocr_run_2026_10_08.csv`. Script as committed at this point:
boxes follow the display, crops scaled to the 10 cm size, segments thickened, H left out
of the time-to-empty box.

What happened (Ron's times, approximate): idle at 84% until AC input unplugged ~12:30 and an
80 W slow cooker plugged in ~12:32; output read 81–82 W and SOC fell 84% → 50% by 13:33
(time-to-empty 2.4H → 1.5H); cooker off ~13:33 (time-to-empty jumped to 22.4H); AC input
back ~13:39 — the plug takes real force and shifted the display ~2 mm, which the boxes
followed; charged at 206–207 W, 50% → 85% by 14:12 (time to full 0.9H → 0.4H); idle 85%,
47.8H after.

| | photos | wrong value | blank (failed read) |
|---|---|---|---|
| all fields | 134 (12:31 excluded: room light on) | 1 — output 81 read as 811 at 12:55 | 3 — time-to-empty at 13:14, 13:45, 14:23 |

The digit 8 — the failure at 10 cm — read right everywhere (47.8, 1.8, 0.8, SOC 58/68/78/80).
SOC skipped 62→64 and 81→83 while charging: at just over 1%/minute with one photo a minute,
that is expected, not a misread.

Found and fixed during the run: with the H inside the box, time-to-empty below 2 hours read
"1.9H" and "1.8H" as "LOH" — the thickened "1" merged with the decimal point. Leaving the H
out fixed it and also improved the 10 cm frames of 2026-10-07 (time-to-empty 13 wrong → 5).

Temperature (Jackery app, open room): 29 °C after ~1 h at 80 W output; 33.9 °C just after
recharging at ~206 W. Charging is the hotter case for the enclosure.
