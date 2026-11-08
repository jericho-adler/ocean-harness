# Ocean Harness — board overview

An **ADAS CAN interposer** for the Fisker Ocean. It splices into the vehicle's main ADAS ECU
connector (CON1) and lets a comma device sit *between* the car and the ADAS ECU — while failing
safe to a plain passthrough whenever it is unpowered.

## Physical arrangement

Five connectors, 89.0 × 72.2 mm, 4 layers, 1.62 mm stackup.

| Side | Connectors | Role |
|---|---|---|
| Vehicle harness | **J3** (20-way Molex 0346910200), **J5** (16-way Molex 0346910162) | plugs into the car harness |
| ADAS ECU | **J4** (20-way), **J6** (16-way) | carries on to the ECU |
| Comma device | **J1** (JAE DX07S024XJ1R1100, 24-pin USB-C shell) | power + CAN |

J3/J4 reproduce CON1 section A and J5/J6 section B. Of the 36 available circuits, 22 are actually
carried.

J1 is a USB-C *connector*, not a USB *port* — it carries 12 V on VBUS and CAN on the TX/RX
differential pairs, comma "OBD-C" style. The CC, D+/D- and SBU2 pins are unused.

## Power

Self-powered from harness VBAT on J3 pin 1 — no external supply.

- **F1** (Bel 0685T3000-01, 3 A time-lag) fuses the board's own tap, leaving the ECU passthrough
  unfused.
- **Q1** (Diodes DMP4015SSS-13 P-channel MOSFET) gives series reverse-polarity
  protection into the `12V_PROT` rail. Drain on the input, source on the output, so the body diode
  conducts battery-to-load and the channel shorts it out; under reversed polarity both block.
  **R7** (100 kΩ) is the gate pulldown and **D15** (BZT52C16) clamps V<sub>GS</sub> to 16 V against
  the ±25 V rating. At 11 mΩ it dissipates 0.1 W at the 3 A fuse limit, where the SS34 Schottky it
  replaced would have dissipated 1.5 W.
- **D9** and **D11** (two SMAJ16A) clamp automotive transients on that rail.
- `12V_PROT` feeds the comma device over all four VBUS pins (A4 / A9 / B4 / B9).
- **R5** (160 Ω) drops `12V_PROT` to the `VIN` rail, which runs the relay coil. At a normal ~14 V
  charging-system rail, R5 against the 960 Ω coil holds it near its 12 V rating. **CR1** (1N4148W)
  is the coil flyback diode and **C2** decouples.

VBAT also passes straight through J3.1 → J4.1 — 1.6 mm leaving J3, 2.4 mm along B.Cu, 2.0 mm into
J4, with six 0.4 mm vias at the layer change — so the ECU keeps its own supply regardless of what
the board is doing. That path is unfused and sits upstream of F1.

### Switch supply

The analog switches get their own rail rather than hanging off the coil supply:

`VIN` → **D12** (DSK14 Schottky) → `SW_IN` → **R6** (3.3 kΩ) → `SW_VCC` → **D13** (BZT52C12, 12 V
Zener) ∥ **C3** (100 nF) → U1/U2 `V+` and `VL`.

D12 blocks backflow when `VIN` dips as the relay coil pulls in, and C3 holds `SW_VCC` up across
that dip. R6 and the Zener clamp the rail to 12 V, so the switches never see the full VBAT range.

## The CAN intercept

This is the point of the board.

**K1** (Omron G5V-2-H1 DC12, DPDT) switches the vehicle's HSCAN1 pair (J3 pins 19/20). Its common
contacts are the *vehicle* side, and the normally-closed contacts go to the ECU:

- **Unpowered** — vehicle ↔ ECU, hard-wired through the relay contacts. Stock car behaviour, the
  comma device is out of the loop entirely.
- **Powered** — the vehicle side is handed to the comma device's `_C` pair (J1 A2/A3). The ECU
  stays permanently wired to the comma's `_MOD` pair (J1 B2/B3), so the device now has the car on
  one port and the ECU on the other.

The `-H1` variant is used for its 150 mW coil (vs 500 mW) and 21.6 V max coil voltage, which
matters because the coil is energised continuously whenever the box is powered.

**U1** and **U2** (Vishay DG419 SPDT analog switches) then decide what happens between those two
segments, under the comma device's `SBU 1` line on J1 A8:

- `SBU 1` **low** — the default; **R2 + R3** form a 240 Ω pulldown. The switches bridge `_C` to
  `_MOD`, so car and ECU are reconnected and the device is only listening. Safe default if the
  device never drives the pin.
- `SBU 1` **high** — the bridge opens and **R4** (120 Ω) is switched across the ECU-side pair
  instead, giving that now-isolated segment its own bus termination. Full man-in-the-middle.

| Power | `SBU 1` | Car ↔ ECU | Comma device |
|---|---|---|---|
| off | — | connected (relay NC) | isolated |
| on | low | connected (via DG419) | listening on both ports |
| on | high | **cut** | in the middle; ECU segment terminated by R4 |

## Straight passthrough

Carried between the harness and ECU connectors, untouched:

- the four corner-radar CANFD pairs (CMRR FR / RR / FL / RL)
- the DMS LED drive
- all six ultrasonic sensor lines (2 × power, power-return and signal)

The mid-range radar CAN passes through with a passive stub tap to J1 A10/A11 so the device can
monitor it.

## Protection

Four **PESD1CAN** ESD arrays, one each on the vehicle-side ADAS CAN (D3), the ECU-side ADAS CAN
(D2), the MRR tap (D8), and the comma-side `_C` pair next to J1 (D1). **D14** (PESD24VS1UB) covers
`SBU 1`.

The four corner-radar CAN FD pairs and the DMS LED pair have no ESD protection, despite landing
directly on vehicle-harness connectors.

## Board construction

| Layer | Use |
|---|---|
| F.Cu | signal + GND pour |
| In1.Cu | GND plane |
| In2.Cu | GND plane, with a `12V_PROT` island (priority) under J1 and a 0.3 mm `VIN` link |
| B.Cu | signal + GND pour |

375 track segments (211 F.Cu, 4 In2.Cu, 160 B.Cu), 65 vias, 0.2 mm minimum track width, 0.3 mm minimum
drill, 73 nets. 35 footprints: 30 components plus two M3 mounting holes and three fiducials.

DRC: 0 errors, 0 unconnected items. 8 schematic-parity items — five `extra_footprint` for the
mounting holes and fiducials, which have no symbol and are expected, and three `Description`/`Spec`
field strings that drift between symbol and footprint. 43 remaining warnings are all cosmetic or
library hygiene — silkscreen clipped by the board edge, silkscreen overlap, and footprint libraries
that are not registered on this machine.

## Notes

- **J1 B10/B11** connect only to the connector and go nowhere else on the board. The `COMMA_P` /
  `COMMA_N` labels that used to name them have been removed; the pins are reserved.
- **J1's row B is through-hole** at 0.65 mm pad on 0.45 mm drill — a 0.10 mm annular ring. Identical
  to the Volvo/Polestar harness box, which is manufactured and in service, so it is proven rather
  than a risk. JAE's drawing specifies a Ø0.4 drill, which would give 0.125 mm.
- **J1's boss 2 is a 1.0 × 0.775 mm milled slot**, not a round hole — JAE's round-plus-slot locating
  scheme, which absorbs the boss-pitch tolerance. A rule in `Ocean Harness.kicad_dru` allows 0.2 mm
  copper-to-edge clearance around it on the outer layers; the rest of the board keeps 0.5 mm.
- **No ignition line.** SBU2 (J1 B8) is unconnected, so the comma device takes ignition from CAN.
- Several datasheets embedded in the board file do not correspond to fitted parts: `DMN3200U-7`
  (the fitted FET is Q1, a DMP4015SSS-13), `JAE MX34032NF4`, `Molex 2125280000`, and `SMAJ36` —
  note the fitted TVS is the **SMAJ16A**, a 16 V standoff part, not the 36 V SMAJ36. Worth
  clearing out; they also add about 3 MB to the file.
