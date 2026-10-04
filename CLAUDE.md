# Jackery display reader

Read the Jackery Explorer 300 Plus front panel with a camera and OCR, locally, so its
state of charge is available during a power outage.

Split out of `../leaf_inverter_rotation` on 2026-10-04. That project owns the rotation
controller; this one owns getting numbers off a screen. Nothing here touches its firmware,
its `loads/*.json` schema, or its control constants.

## Why this exists

Not convenience. In the parent project's `docs/jackery_300_plus.md` §13, state of charge is
the **control variable** for the whole scheme:

The kitchen fridge runs behind the Jackery as a buffer, so the rig's current sensor is
blind to it. The rotation's time budget is over 100% once the furnace is included, and the
Jackery is the only interruptible load — so it is the one that gets squeezed. It then loses
ground at **8–33 Wh/h** and eventually hits its **15% output cutoff, which drops the fridge
with no warning**, somewhere between ~6 h and ~25 h in.

Nothing else can see that coming. Wall-side current cannot distinguish "holding steady"
from "slowly losing." **SOC is what says which side of break-even the rotation is on**, and
it drives a concrete decision: give the Jackery a bigger share, or move the fridge to direct
inverter power before the cutoff.

## Inherited facts — hard-won, do not relitigate

From `../leaf_inverter_rotation/docs/jackery_300_plus.md` §9–§13. Each cost real time.

1. **"Input" on the display means charge INTO THE BATTERY, not draw from the wall.**
   Established 2026-09-30 by simultaneous readings: the display read input 0 W while a
   clamp meter showed 0.66 A flowing in the AC cord. **Consequence: the display cannot
   distinguish "charger unplugged" from "battery full."** Both read 0 W.

2. **Time-to-empty is a VALID instantaneous estimate and is worth reading.** It is
   (remaining Wh) ÷ (present total draw), confirmed across a 75× range of output:

   | output | time-to-empty | implied draw |
   |---|---|---|
   | 1 W | 37 h | 6.5 W |
   | 52 W | 3.3 h | 73 W |
   | 75 W | 2.3 h | 103 W |

   Linear: draw = 1.30 × output + 5.2 W. In an outage it reprices against real load — at
   51 W output it reads ~3.5 h, not 37 h. **Arguably more actionable than SOC itself.**
   Its "time to full" while charging is NOT coherent; only the discharge estimate is.

3. **The unit resumes charging on its own.** Confirmed 2026-10-01 by a zero-touch overnight
   observation: 81% at 22:44 → 85% at 04:46, nothing touched. Resume threshold bounded only
   as ≤ 81%.

4. **The app was a dead control path; as of 2026-10-04 it works again.** Every connection
   attempt used to end in a "connecting Bluetooth" timeout. On 2026-10-04 the app connected
   and toggled settings normally. Ron suspects a power cycle of the Jackery cleared it — not
   tried before because the unit was in use. Its Wi-Fi goes to Jackery's cloud, which is
   gone in an outage anyway, so the app is for setup, not for reading during an outage.

5. **The Screen timeout setting should now be reachable through the app.** The app offers
   2 hr / 2 m / Off. Which is set is still unknown. **This is the blocking unknown for the
   whole approach** — see Open questions.

6. **Battery Save mode:** charging stops at 85%, output cuts at 15%. Usable window 70% ≈
   202 Wh of a 288 Wh pack.

## Prior art — `philippbussche/jacktessery`

Same problem, Explorer 1000 Pro. ESP32-CAM photographs the panel, POSTs the JPEG to a Flask
API. Read 2026-09-30; worth knowing in detail because it works.

- **No OpenCV, no machine learning.** ~25 lines of Pillow: greyscale → threshold at 230 →
  crop to a fixed region of interest → dilate (3×3 max filter) → invert → add a 10 px white
  border then a 5 px black border → Tesseract.
- **Tesseract DOES read seven-segment digits with the right model:** `lang =
  ssd_alphanum_plus`, `--psm 8`. Plain Tesseract is poor at them; that tessdata plus a tight
  region of interest is a legitimate route and less work than hand-rolled segment decoding.
- **The validation layer is the real engineering content.** Per value: `max_value`,
  `max_rate` with a 900 s grace period, `min_confidence` floored at 60, and revert to the
  last good value on a failed read. **That this was necessary says the OCR misreads
  regularly. Plan for it.**
- **A tell:** only SOC was shipped enabled. `input_watts` and `output_watts` were configured
  and switched off, with input's confidence floor dropped to 20. Read that as: the large SOC
  digits are gettable, the smaller fields were not reliable enough.
- Its timeout workaround was a Fingerbot glued to the USB-output button on four daily
  schedules — two readings per day.

Region-of-interest coordinates are per-model and per-mounting. The 1000 Pro's numbers
transfer nothing but the method.

## Hardware on hand

- **RPi 3B v1.2** — the intended host. Onboard Wi-Fi, quad-core, 1 GB, CSI connector clear.
- RPi 4 in an Argon ONE V2 case — sealed enclosure; whether the camera ribbon routes out of
  it cleanly is unchecked.
- 2 × Model B Rev 2 (2012) — ARMv6, 512 MB, no Wi-Fi. Have CSI but are the wrong end of the
  range for Tesseract.
- 5 further Pis, unidentified. Worth identifying — a Zero W would be the better long-term
  form factor on top of a fridge.
- **Camera Module v1.3** (OV5647, 5 MP) and **v2.1** (IMX219, 8 MP). Both fixed focus.
- A cobbler.

A Pi collapses jacktessery's two boxes into one: capture, Pillow, Tesseract, validation and
reporting on the same machine, and GPIO for a wake actuator if one is needed.

## Interface back to the parent project

**One-way sender into the `dual_logger` listener** — same clock, same line format, per
`../leaf_inverter_rotation/docs/dual_logger_socket_ingest.md`. Fix this before writing
much; two halves that don't quite meet is the main risk of having split the projects.

## Open questions

Blocking, in order:

- [ ] **Does the screen stay lit long enough to photograph on a schedule?** Measure the
      current timeout by observation: wake it, note which button, time how long until dark.
      **2 hours** makes a wake actuator a convenience; **2 minutes** makes it the
      reliability bottleneck — an overnight outage needs hundreds of actuations.
- [ ] **Can the Screen timeout be set from the unit's own buttons**, bypassing the dead app?
      This is the outcome to hope for.
- [ ] **Does taking the unit's Wi-Fi away bring Bluetooth back?** A MAC filter on the
      gateway, reversible. The parent project's `docs/jackery_300_plus.md` has the MAC
      recorded two ways, one of them a digit short — read it off the gateway.
- [ ] **Focus distance.** Both camera modules are fixed focus, nominally 1 m to infinity. A
      panel shot at 15–25 cm comes out soft, and soft seven-segment digits are exactly what
      Tesseract fails on. Either stand back ~1 m and crop, or rotate the lens (the v1.3's
      OV5647 is the one generally reported adjustable). **Measure the SOC digit height with
      a ruler first** — at ~1 m both modules give ~2.6–2.7 px/mm, and Tesseract wants ~40 px
      of digit height, so that needs digits ≥ ~15 mm.
- [ ] Standing cost of a lit display. Probably under a watt, but against a 288 Wh pack it is
      worth a number rather than a shrug.

Design notes, not blocking:

- **The Pi is powered from the unswitched power strip, with its own adapter — not from the
  Jackery.** Decided 2026-10-04. The strip also feeds the gateway and other small loads, is
  never switched by the rotation, and in production arrives on its own extension cord from
  the basement rig, ending near the fridge cord. This keeps the Pi's draw out of the
  Jackery's usable window and keeps the Jackery's USB output off, as Ron runs it in outages.
  It also sidesteps two traps: a camera fed from the USB port it presses would cut its own
  supply on every wake (jacktessery's Fingerbot pressed the USB button because nothing was
  on USB), and USB output auto-shuts off after 12 h at ≤ 2 W.
  Optional: a Kill A Watt in front of the Pi's adapter would give the standing cost.
- Rigid mounting is load-bearing: if the camera shifts, every region of interest breaks.
- A shroud is needed against glare on the panel.
- Ron has hobby servos. A bracket the Jackery sits in is preferred over anything glued to
  the case.
- **Battery discharge rate is not on the display at any load** — "input" reports charge in
  only. SOC trend over time is the only way to see it, which argues for logging SOC
  continuously rather than sampling it.

## Conventions

Carried from the parent project; they are Ron's, not this repo's.

- **Underscore naming** for all files and folders.
- **Never coin shorthand or jargon labels** — in prose, in keys, in commit messages. Use
  plain words or ask. Emphatic standing rule.
- **One step at a time.** Give one step, wait for confirmation. Do not stack six steps.
- **Follow the data, not the hypothesis.** Pull the raw file before asserting a diagnosis.
- **Do not assert the existence or behaviour of hardware, parts or libraries without
  checking first.**
- Mark confidence honestly; prefer measured values to assumed ones.
- Append to notes files with `cat >>`, never `cat >`.
- Record hardware quirks as code comments where they apply, not only in docs.
- Short replies. One subject at a time; let Ron pull the next.

### Instrument names, as Ron set them

- **the Ammeter** — the ESP32 + ADS1115 + ACS712 node, cord-and-plug with molded ends
- **the DMM** — the KAIWEETS multimeter
- **the EXTECH** — the clamp meter (30 A / 4000 mA / 400 mA, has MAX but auto-powers-off)
