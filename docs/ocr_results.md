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
