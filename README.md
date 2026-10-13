# Ocean Harness

An automotive ADAS harness interposer designed in KiCad, built for the **Fisker Ocean**. It sits inline on the main ADAS ECU connector (CON1) and provides a fail-safe electrical bypass plus signal switching for a comma device, protected against automotive power-rail transients and ESD.

![Assembled board render, showing the harness-side and ECU-side connectors](3D%20models/Ocean%20Harness.png)

- **Board:** 115.75 × 75.25 mm, 4-layer (F.Cu / In1.Cu=GND / In2.Cu / B.Cu), 22 components across 27 footprints (the extra five are two M3 mounting holes and three fiducials, none of which have a schematic symbol), 69 nets
- **Harness interposition:** the vehicle harness lands on **J3 + J5**; **J4 + J6** carry on to the ADAS ECU. J3/J4 are 20-circuit (CON1 section A) and J5/J6 are 16-circuit (CON1 section B), so the board reproduces all 36 used pins of the Fisker pinout
- **Power:** self-powered from harness VBAT (pin 1A) — no external supply needed. Reverse-protected by an SS34 Schottky into a `12V_PROT` rail, TVS-clamped by two SMAJ16A, and passed to the comma device over USB-C VBUS
- **Fail-safe passthrough:** a DPDT relay (Omron G5V-2-H1 DC12) wired so the normally-closed contacts connect the vehicle CAN (HSCAN1, pins 19A/20A) straight through to the ECU when the box is unpowered, and hand it to the comma device when energised. The coil runs off `12V_PROT` through a 160 Ω dropper (R5) that holds it at its 12 V rating across the DC-DC output range; the high-sensitivity `-H1` variant is used for its 150 mW coil (vs 500 mW) and 180% max coil voltage (21.6 V), which matters because the coil is energised continuously whenever the box is powered
- **Signal switching:** two DG419 SPDT analog switches route the CAN pairs under control of an `SBU 1` logic input from the comma device, with a switched 120 Ω bus termination (R4)
- **Protection:** PESD1CAN ESD diodes on the intercepted and tapped CAN lines
- **Pass-through only:** the four corner-radar CANFD pairs, the DMS LED drive, and all six ultrasonic sensor lines run straight across the board untouched; the mid-range radar CAN is passed through with a listen-only tap to the comma device

## Design review

[`PCB Files/design_review_2026-10-13.md`](PCB%20Files/design_review_2026-10-13.md) — **current.** Full analyser-backed review of functional correctness and production readiness, cross-checked against the Fisker CON1 pinout and against a confirmed-working reference design. Verdict: the board functions, and the five pre-fab blockers it identified have been fixed. Read it before fabricating — it still lists the items to confirm before installing in a vehicle, chiefly verifying the Molex connector pin numbering and polarization against the Fisker CON1 keying.

[`PCB Files/design_review_2026-10-12.md`](PCB%20Files/design_review_2026-10-12.md) — superseded; kept for history. Note that two of its claims do not match the committed board: the VBAT pass-through measures 61 mΩ rather than 24.6 mΩ, and its "DRC 0 unconnected" result held only after a zone refill.

## License

Licensed under the [CERN Open Hardware Licence Version 2 - Strongly Reciprocal](LICENSE) (CERN-OHL-S-2.0).

## Disclaimer

This is a community hardware design shared as-is, with no warranty. It is designed specifically for the Fisker Ocean — using it on other platforms is unverified. **Use at your own risk.** Read the current design review before fabricating or installing in a vehicle — in particular its "Confirm before installing" items, which cannot be settled from the design files alone.
