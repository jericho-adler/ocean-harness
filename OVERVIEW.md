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

- **D10** (SS34 Schottky) gives series reverse-polarity protection into the `12V_PROT` rail.
- **D9** and **D11** (two SMAJ16A) clamp automotive transients on that rail.
- `12V_PROT` feeds the comma device over all four VBUS pins (A4 / A9 / B4 / B9).
- **R5** (160 Ω) drops `12V_PROT` to the `VIN` rail, which runs the relay coil. At a normal ~14 V
  charging-system rail, R5 against the 960 Ω coil holds it near its 12 V rating. **CR1** (1N4148W)
  is the coil flyback diode and **C2** decouples.

VBAT also passes straight through J3.1 → J4.1 on 1 mm copper, so the ECU keeps its own supply
regardless of what the board is doing.

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

Four **PESD1CAN** ESD arrays, one each on the vehicle-side ADAS CAN, the ECU-side ADAS CAN, the MRR
tap, and the `COMMA_P` / `COMMA_N` pair.

## Board construction

| Layer | Use |
|---|---|
| F.Cu | signal + GND pour |
| In1.Cu | GND plane |
| In2.Cu | split power plane — `12V_PROT` (priority) over `VIN` |
| B.Cu | signal + GND pour |

353 track segments, 57 vias, 0.25 mm minimum track width, 0.3 mm minimum drill, 71 nets.
31 footprints: 26 components plus two M3 mounting holes and three fiducials.

DRC: 0 errors, 0 unconnected items, 0 schematic-parity issues. 32 remaining warnings are all
cosmetic or library hygiene — silkscreen clipped by the board edge, silkscreen overlap, and
footprint-library mismatches.

## Notes

- **`COMMA_P` / `COMMA_N`** (J1 B10/B11) connect only to the connector and their TVS diode — they
  go nowhere else on the board. Reserved, or a leftover.
- The `DMN3200U-7.pdf` in the board file's `embedded_files` block is an orphaned datasheet
  attachment; there is no MOSFET on this board. Several other embedded datasheets (`JAE
  MX34032NF4`, `Molex 2125280000`, `SMAJ36`) likewise do not correspond to fitted parts.
