# Display indicators

What the Explorer 300 Plus panel symbols mean, established by observation. Where this
disagrees with the manual (`reference/`), this file wins: each entry was checked on the unit.

## 2026-10-04 — checked by Ron, toggling settings from the app and watching the panel

**The manual is wrong about Battery Saver Mode's indicator.**

- **Battery Saver Mode** is the **white battery icon** just outside the ring at about
  11 o'clock. The manual says it is the "12H" inside the ring. Checked by toggling Battery
  Saver Mode from the app.
- **"12H"** (inside the ring at 12 o'clock) is the **output auto-off setting**: the unit
  turns its output off after 12 hours at no load or light load. Other settings are 8H,
  24H and Never. It lights when any output is on:
  - AC output on → lights "12H", time to 0%/15%, and the AC indicator (orange sine wave in
    a circle, outside the ring at about 1 o'clock).
  - DC/USB output on, by itself → lights "12H" and time to 0%/15%.
  - Both on → "12H" lit.
- Consequence for reading the screen: the time-to-empty field is only shown when an output
  is on.

### The manual's own description of the "12H" setting (it calls it Energy Saving Mode)

From the manual, which agrees with what Ron found. All outputs turn off after 12 hours
when nothing is connected, or when the load is at or below:

| output | threshold |
|---|---|
| AC | ≤ 25 W |
| USB | ≤ 2 W |
| car | ≤ 2 W |

It can be turned on and off **from the unit's own buttons**: long-press the AC button and
the main power button together until the icon goes out (off) or lights (on).

Open, not stated in the manual: whether the 12 hours must be continuous below threshold
(so each fridge compressor run restarts the count) or is counted some other way.

## 2026-10-07 — charging seen by the Pi camera (bench run, one frame a minute)

Jackery plugged into the wall at ~14:08, no load on any output, Battery Save on.

| time | SOC | input | under input | time-to-empty field |
|---|---|---|---|---|
| 14:14 | 81% | 0W | — | 45.5H |
| 14:15 | 80% | 200W | 0.4H | 99.9H |
| 14:16 | 81% | 206W | 0.4H | 99.9H |
| 14:17 | 82% | 207W | 0.4H | 99.9H |
| 14:18 | 83% | 207W | 0.4H | 99.9H |
| 14:19 | 84% | 206W | 0.4H | 99.9H |
| 14:20 | 85% | 0W | — | 47.8H |

- **Charging resumed when SOC reached 80%** (Ron predicted ≤ 80%), and stopped at the
  85% Battery Save ceiling. Tightens the parent project's "resume ≤ 81%" to "at 80%" —
  one observation.
- ~205 W input, ~1% per minute; the whole top-up took 5 minutes.
- **While charging, a time field appears under input (0.4H, time to full) and the
  time-to-empty field reads 99.9H** — apparently a placeholder, not an estimate. The
  reader must not treat 99.9H as a real time-to-empty.
- The top-right voltage read **124V** in charging frames and **120V** in earlier frames
  that day. What it measures is not established.
- At 0 W output and 81%, time-to-empty read 45.5H, implying ~5 W standing draw
  (0.81 × 288 Wh ÷ 45.5 h).
