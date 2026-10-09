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

### Looked at, not adopted

- **`SachaIZADI/Seven-Segment-OCR`** (read 2026-10-06). A 2018 class project reading
  fuel-pump displays from ~850 handheld phone photos with trained neural networks. Its
  hard problem — finding the screen in a hand-held photo — does not exist with a fixed
  camera; it needs hundreds of labelled images and a machine learning stack on the Pi; its
  "how to reproduce" section is unfinished. Tesseract already read the fields.
- **If Tesseract fails on Pi camera images**, the next thing to try is not a trained model
  but checking each segment's fixed pixel position for lit/unlit and looking up the digit
  — possible only because the camera is fixed. `ssocr`
  (https://www.unix-ag.uni-kl.de/~auerswal/ssocr/) is an existing tool for this; untried.

## Hardware on hand

- **RPi 3B v1.2** — the intended host. Onboard Wi-Fi, quad-core, 1 GB, CSI connector clear.
  **State as of 2026-10-06:** reflashed with Raspberry Pi OS Lite, Debian 13 (trixie),
  64-bit. Hostname `camera`, user `pi`, at 192.168.1.217 on Wi-Fi (address from DHCP, not
  reserved). SSH is key-only, with Ron's Mac key. First boot showed "Failed to start
  userconfig.service" once; the `pi` user and sudo work and no units are failed, so it
  was harmless. Camera (v2.1) unplugged and bagged. `sudo` asks for Ron's password (not
  passwordless). **2026-10-07:** Tesseract 5.5.0 and Pillow 11.1.0 from apt; `7seg` and
  `ssd_alphanum_plus` models in `~/tessdata`. The phone-photo test reads the same as on
  the Mac (85, 53W, 3.3H, OW) at **about 0.4 s per field** with `7seg`. The card's previous contents (2023 picamera2 tutorial scripts and test images)
  are in `captures/old_camera_card_2023/`.
- **SD cards:** the Pi 3B's card is the one above. A second good card holds Raspberry Pi
  OS from 2021 (Buster, desktop, HDMI forced to 1080p) — contents not inspected. A third
  card is dead (not detected in three readers).
- RPi 4 in an Argon ONE V2 case — sealed enclosure; whether the camera ribbon routes out of
  it cleanly is unchecked.
- 2 × Model B Rev 2 (2012) — ARMv6, 512 MB, no Wi-Fi. Have CSI but are the wrong end of the
  range for Tesseract.
- 1 × Model B Rev 1 — identified 2026-10-06 and labelled on its Ethernet jack: board
  printed only "Raspberry Pi (c)2011", has Ethernet, no mounting holes. 256 MB, ARMv6, no
  Wi-Fi. Not a candidate host.
- 4 further Pis, unidentified. Worth identifying — a Zero 2 W would be the better long-term
  form factor in the box (needs the narrower camera ribbon).
  How to tell the 2012-era boards apart: printed "(c)2011" or "(c)2011.12" only; no
  Ethernet = Model A; Ethernet and no mounting holes = Model B Rev 1; Ethernet and two
  mounting holes = Model B Rev 2.
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

- [x] **Answered 2026-10-07 (one run):** a **double click of the power button puts the
      screen always on**. A short press wakes it. After Ron double-clicked before the run, a
      once-a-minute photo run from 14:09 to 17:08 found the screen lit in all 180 frames
      (blue-pixel count never below 96,519; dark reads near 0) — over 3 hours, longer than
      the app's 2-hour setting, nothing touched. Not yet known: whether always-on survives
      a power cut or the unit's own restart.
- [ ] **Does the screen stay lit long enough to photograph on a schedule?** Measure the
      current timeout by observation: wake it, note which button, time how long until dark.
      **2 hours** makes a wake actuator a convenience; **2 minutes** makes it the
      reliability bottleneck — an overnight outage needs hundreds of actuations.
- [ ] **Can the Screen timeout be set from the unit's own buttons**, bypassing the dead app?
      This is the outcome to hope for.
- [ ] **Does taking the unit's Wi-Fi away bring Bluetooth back?** A MAC filter on the
      gateway, reversible. The parent project's `docs/jackery_300_plus.md` has the MAC
      recorded two ways, one of them a digit short — read it off the gateway.
- [ ] **Focus distance — now a bench test of the v2.1.** Measured by Ron 2026-10-07 with a
      ruler: whole display 26 × 45 mm; SOC digits 5 mm tall × 3 mm wide; time-to-empty
      digits 2 mm tall × 1 mm wide. (A phone photo agrees: digit heights in ratio 2.4.)
      The v2.1 covers ~1.2 × distance across 3280 px, so for ~40 px of digit height:
      SOC needs ≤ ~34 cm, **time-to-empty needs ≤ ~14 cm** — the small digits set the
      distance. At 1 m the SOC digits are only ~14 px, so standing back is out.
      Both modules ship focused 1 m to infinity. **Correction:** the v2.1 is the one made
      to be refocused (a lens adjustment tool exists for it); the v1.3's lens is glued and
      Arducam warns forcing it can damage the module. Test: refocus the v2.1 at ~14 cm and
      closer, and see how close it goes sharp. The display is so small that closer than
      14 cm still fits the frame; the limit is the lens.
      **Bench result 2026-10-07 (Jackery on the lathe ways, camera in a PanaVise):** with
      the v2.1 lens turned ~90° counterclockwise by hand (no tool; unscrewing focuses
      closer, as the forum said; Ron may have scratched the lens doing it), **10 cm is
      sharp enough to read every field by eye**: display ~1150 px wide (~26 px/mm), SOC
      digits ~130 px, small digits ~50 px. 15 cm was readable for SOC only; 30 cm soft.
      Camera settings used: `--rotation 180 --shutter 50000 --gain 4 --awbgains 1.5,1.5`
      in a dark room (automatic exposure blooms the lit segments into blobs). The white
      segments read BLUE and the orange ring RED to this camera — use the blue channel.
      First Tesseract pass with hand-guessed boxes got SOC/input/output right after
      letter-for-digit fixes; time-to-empty was clipped by a too-tight box. Boxes now
      tuned (`src/read_fields.py`); over the run's 180 frames SOC was right in all 180,
      time-to-empty wrong in 19 (8 read as 9). See `docs/ocr_results.md`.
      Photos: `~/run_2026_10_07/` on the Pi.
      **2026-10-08: the lens is focused near 7 cm, not 10.** A 5–9 cm sweep read every
      field at 6–9 cm; 7 cm sharpest. A 2-hour run at 7 cm through idle, an 80 W load and a
      recharge: 1 wrong value and 3 blanks in 670 readings. **Use 7 cm.** See
      `docs/ocr_results.md`. Not yet done: a printed-text check for the possible scratch.
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
- **Watch for changes, not only poll SOC** (Ron, 2026-10-04). Frame comparison per region
  is far cheaper than OCR, so the Pi can watch at a few frames a second and OCR only what
  changed. (3B throughput not measured.) Changes worth catching, most important first:
  1. Output to 0 / AC indicator out — the 15% cutoff or 12 h auto-off actually happening,
     i.e. the fridge dropped. Alarm within seconds instead of finding out later.
  2. Input appearing or disappearing — charger resumed or stopped; pins down the resume
     threshold, bounded only as ≤ 81%.
  3. Output stepping up and down — compressor starts and stops, giving fridge duty cycle,
     which the rig's current sensor cannot see.
  4. Screen going dark — the reader's own problem: wake it or flag the gap.
  5. Anything unexpected (new icon, unreadable field) — save the frame for a person.
  Depends on the screen staying lit; see the timeout question.
- **Enclosure** (Ron, 2026-10-04): the Jackery and camera in a light-tight, fan-ventilated
  box of thin plywood. Self-lit display in the dark gives constant lighting and no glare.
  Internal heat ≈ 0.3 × output + 5 W from the inherited draw fit (~21 W at 53 W output),
  plus unmeasured charging loss; align box airflow with the Jackery's own vents; light-tight
  vents via black-painted baffles. Non-metal skin so Wi-Fi/Bluetooth still reach the unit.
  **Outside display:** first a web page served by the Pi (phone on the LAN), then a small
  screen on the box showing the latest raw photo of the panel.
  **Construction** (Ron, 2026-10-08): a stiff base of ¾" hardwood plywood with everything
  fastened to it — Jackery, camera, Pi — and a cover that comes down over it from above,
  guided as it drops, like a cake cover. Camera-to-display alignment then depends only on
  the base. Open points: cords (AC input, fridge output, Pi power) through grommeted holes
  in the base rather than notches in the cover; stops or a cradle that hold the Jackery
  against the charging cord's push (attaching it takes real force and shifted the display
  ~2 mm on 2026-10-08); a light-tight joint where the cover meets the base. The cover must
  lift off easily: turning on AC output undid screen always-on on 2026-10-08, so the power
  button needs pressing now and then. App showed the Jackery at 29 °C after ~1 h at 80 W
  output, open room, and **33.9 °C just after recharging 50% → 85% at ~206 W** — charging
  is the hot case. **Rating label** (`docs/images/rating_label.jpg`, 2026-10-08): charge temperature 0–45 °C,
  discharge −10–45 °C; LiFePO4, 22.5 Ah / 12.8 V (288 Wh), model JE-300B. Whether 45 °C
  means room temperature or the internal temperature the app shows is not stated; if the
  latter, charging in the open room leaves ~11 °C. Closed-box test: charge from ~50% with
  the cover on and watch the app's temperature.
- **Alternative to the box: a hood** (Ron, 2026-10-09), like old oscilloscope cameras — a
  3D-printed shroud joining the camera module to the display and keeping light out. Ron
  judges it too complex for him; recorded for others. Gains: the Jackery stays in open air
  (no ventilation problem), camera is held to the display itself, small and shareable as a
  print file. Must handle: attachment without glue (clip or strap), leaving the power and
  light buttons beside the display reachable, and stray reflection — matte black ribbed
  or flocked interior, and a black plate around the lens so the camera board does not
  reflect in the display glass (that last point applies to the box too).
- Rigid mounting is load-bearing. Since 2026-10-08 the boxes follow the display when it
  shifts or changes size, but **not when it rotates**: the camera is rolled ~2.5° and the
  boxes were measured with that roll; ~1° more moves the time-to-empty box ~25 px at 7 cm,
  past its margin. Hold roll to within ~0.5°. Automatic rotation correction (measure the
  roll from the SOC digits' top edges, turn the photo level) was offered and deferred —
  Ron may make the camera mount adjustable instead. Next step (Ron, 2026-10-08): a
  prototype box to work out holding the Jackery and the camera in place.
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
