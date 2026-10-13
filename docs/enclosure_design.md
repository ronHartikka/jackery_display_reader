# Enclosure and camera mount — design facts

Gathered 2026-10-13 for the CAD drawing of the Jackery, Pi and camera assembly. The box's
overall plan (plywood base, cake-cover lid, cords, ventilation, temperatures) is in
`../CLAUDE.md` under Design notes → Enclosure; this file holds the dimensions and decisions
for holding the parts in place.

## Requirements the camera sets

- **Distance: 7 cm, lens face to display face.** Every field read from 6 to 9 cm (sweep of
  2026-10-08, `ocr_results.md`); 5 cm was softer. The lens is focused near 7 cm.
- **Lens height = height of the display's centre** above whatever the Jackery stands on.
- **Roll held to within ~0.5°.** The reader follows the display when it shifts or changes
  size, not when it rotates; ~1° moves the time-to-empty box ~25 px at 7 cm.
- **Pitch and yaw:** square to the display by eye; a few degrees only makes the display
  slightly wider at one end.
- **A matte black plate around the lens**, so the camera board and the white ribbon do not
  reflect in the display glass.

## Jackery feet (measured by Ron)

- Four rubber feet, diameter **0.980" ± 0.002"**, height **0.100" ± 0.002"**.
- Flat within about 0.4" of the centre.
- Centres on a **6.1" × 3.2"** rectangle (probably 6.100" × 3.200"; not measurable to that).

## Locating plate (Ron's design, 0.125" ABS sheet, drill press only)

- An **8" × 5"** plate, plus four **1.5" squares** each with a **1" hole**. The squares are
  glued to the plate with the Jackery's feet sitting in the holes, so the feet locate the
  squares rather than the drilling doing it.
- The squares (0.125") are thicker than the feet stand proud (0.100"): put a 0.03–0.05"
  spacer in each hole so the Jackery rests on its feet, not on the squares.
- Drill the 1" holes before cutting the squares out.
- Ron's addition: **extend the plate forward to carry the camera mount**, so the camera
  and the Jackery are located by the same piece. Screw the extension to the plywood along
  its length; 0.125" ABS cantilevered a few inches would flex.

## Mock-up, 2026-10-10

- **The Jackery is raised** on blocks so the Pi 3B lies flat underneath it, its ports
  reachable at the front.
- **The camera mounts on an ABS box** tall enough to put the lens at display height, on
  standoffs from the box wall. The standard ribbon reaches from the Pi.
- **Adjustment:** the box's mounting to the base allows five adjustments — everything but
  roll. **Roll is set between the box and the camera board**: one screw as a pivot, the
  other in a slot, or a fine screw pushing the board. 0.5° over the board's hole spacing is
  a few tenths of a millimetre at the slot end.
- **Test photo from the mock-up:** display 1620 px wide (= 7 cm), roll ~0.6°. Wi-Fi works
  with the Pi under the Jackery.
- **The camera is now mounted upside down** compared with the bench: capture without
  `--rotation 180`.
- SOC and input read correctly; output did not, because the boxes in `src/read_fields.py`
  were measured with the bench's 2.5° roll. **Re-measure the boxes once the final mount is
  set**, rather than rolling the camera back to 2.5°.

## Alternatives considered

- **Glued LEGO bricks** as a platform (ABS, so solvent-welds to the ABS plate; precise and
  square without cutting). Fine roll adjustment would still need a pivot and slot at the
  camera board. Superseded for now by the ABS box.
- **A 3D-printed hood** instead of a box — see `../CLAUDE.md` and the README.

## Part dimensions — check before drawing

Not measured here; take from the makers' drawings or a caliper:

- Raspberry Pi 3B board outline and mounting holes.
- Camera Module v2.1 board outline, hole positions and lens position.
- Jackery body outline and the display's position on the front.
