# Ocean Harness

An ADAS CAN interposer for the **Fisker Ocean**, designed in KiCad. It plugs in between the car's harness and the ADAS ECU's main connector (CON1), so a comma device can sit between the car and the ECU. When the board has no power it drops back to a plain hard-wired passthrough, and the car behaves exactly as stock.

![Isometric render of the board, showing the stacked vehicle-harness and ADAS-ECU connectors around the relay and USB-C connector](images/ocean-harness-iso.png)

| | |
| --- | --- |
| Board | 89.0 × 72.2 mm, 4 layers, every part on the top side |
| Parts | 30 components, plus two M3 mounting holes and three fiducials |
| Mounting | One M3 hole in each gap between the stacked headers |
| Power | Taken from the harness VBAT on J3 pin 1. No external supply |
| Comma link | USB-C (J1) carrying 12 V and CAN, comma "OBD-C" style. It's not a USB data port |
| Revision | Rev 2, November 2026. New layout, not yet built |

## Connectors

| Ref | Part | Side | Carries |
| --- | --- | --- | --- |
| J3 | Molex 0346910200, 20-way | Vehicle harness | CON1 section A |
| J5 | Molex 0346910162, 16-way | Vehicle harness | CON1 section B |
| J4 | Molex 0346910200, 20-way | ADAS ECU | CON1 section A |
| J6 | Molex 0346910162, 16-way | ADAS ECU | CON1 section B |
| J1 | JAE DX07S024XJ1R1100, USB-C | Comma device | 12 V, three CAN pairs, one control line |

The harness side is on the right edge ("CAR HARNESS-->") and the ECU side is on the left ("<--ADAS ECU"). 22 of the 36 CON1 circuits are carried. Every other pin is left unconnected.

## How it works

### Power

VBAT comes in on J3 pin 1. It goes straight through to J4 pin 1 (1.6 mm leaving J3, 2.4 mm along B.Cu, 2.0 mm into J4, with six 0.4 mm vias at the layer change), so the ECU keeps its own supply whatever the board is doing.

The board takes its own power from the same feed through F1 (Bel 0685T3000-01, 3 A time-lag, 63 V), so a short anywhere on the board side opens F1 rather than the car's fuse for the ECU. `VBAT_FUSED` then goes to Q1 (Diodes DMP4015SSS-13 P-channel MOSFET), which blocks reverse polarity into the `12V_PROT` rail. D9 and D11 (two SMAJ16A) clamp transients on that rail, and C1 decouples it. `12V_PROT` powers the comma device through all four USB-C VBUS pins.

Q1 is wired drain-to-input, source-to-output, so its body diode conducts battery-to-load and the channel then shorts it out. R7 (100 kΩ) pulls the gate to ground, which holds the FET hard on whenever `12V_PROT` is up; under reversed polarity the source collapses with it, V<sub>GS</sub> goes to zero and the FET — and its body diode — both block. D15 (BZT52C16, 16 V zener) clamps V<sub>GS</sub>: without it the gate would sit at the full battery voltage and exceed the ±25 V rating when D9/D11 clamp a transient at around 26 V.

At 11 mΩ this drops 0.1 W at the 3 A fuse limit, against 1.5 W for the SS34 Schottky it replaces, and hands about 0.4 V of headroom back to the comma device.

R5 (160 Ω) drops about 2 V from `12V_PROT` to make `VIN`, which runs the relay coil. That holds the coil near its 12 V rating on a 14 V running rail. CR1 (1N4148W) is the coil's flyback diode, and C2 decouples `VIN`.

The analog switches get their own clamped supply. `VIN` runs through D12 (DSK14) and R6 (3.3 kΩ) to `SW_VCC`, where D13 (BZT52C12) holds it to about 12 V and C3 decouples it. `SW_VCC` feeds both V+ and VL on U1 and U2. This clamp is the one used on the Volvo/Polestar harness box, and rev 2 added it for three reasons:

- The DG419LE is rated for a 3 to 16 V supply (18 V absolute max). The SMAJ16A clamps don't start conducting until 17.8 V, so without D13 the switches could sit outside their rating on a high input.
- D12 stops current back-feeding into `VIN` through the switches' internal clamp diodes when the board is unpowered but the car bus is live.
- R6 keeps the standby draw to about 0.6 mA at 14.4 V.

### The CAN intercept

K1 (Omron G5V-2-H1 DC12, DPDT) switches the vehicle's ADAS CAN (HSCAN1, J3 pins 19/20). Its common contacts are on the vehicle side and its normally-closed contacts go to the ECU, so with no power the car and ECU are hard-wired together and the comma device is out of the loop.

Once the board has power, the relay moves the vehicle side over to the comma device's `_C` pair (J1 A2/A3). The ECU stays wired to the device's `_MOD` pair (J1 B2/B3), so the device has the car on one port and the ECU on the other. The coil is energized the whole time the board has power. The `-H1` variant is used for its 150 mW coil (against 500 mW for the standard part) and its 21.6 V maximum coil voltage.

U1 and U2 (Vishay DG419LE SPDT analog switches) decide what happens between the two segments. The comma device controls them through `SBU 1` on J1 A8.

With `SBU 1` low, the switches bridge `_C` to `_MOD`, so the car and ECU stay connected and the device only listens. That's the default: R2 + R3 form a 240 Ω pulldown, so it's also the safe state if the device never drives the pin.

With `SBU 1` high, the bridge opens and R4 (120 Ω) is switched across the ECU-side pair, so that segment keeps its own termination. The device is now fully in the middle.

| Power | `SBU 1` | Car ↔ ECU | Comma device |
| --- | --- | --- | --- |
| Off | Any | Connected through K1's normally-closed contacts | Isolated |
| On | Low | Connected through U1/U2 | Listening on both segments |
| On | High | Cut. The ECU segment is terminated by R4 | In the middle |

### Straight passthrough

These run between the harness and ECU connectors untouched:

- the four corner-radar CAN-FD pairs (CMRR FR, RR, FL, RL)
- the DMS LED drive
- all six ultrasonic sensor lines (power, power return and signal for USS1 and USS2)
- ground on pin 14

The mid-range radar CAN (MRR) also passes straight through. It has a passive stub tap to J1 A10/A11 so the device can monitor it.

### Protection

Four PESD1CAN ESD arrays protect:

- D3, the vehicle-side ADAS CAN
- D2, the ECU-side ADAS CAN
- D8, the MRR tap
- D1, the `_C` pair (J1 A2/A3), next to J1

D14 (PESD24VS1UB) protects `SBU 1`. The reserved `COMMA_P`/`COMMA_N` pair has no ESD diode now that D1 has moved.

F1 fuses the board's tap off VBAT. Reverse polarity and transients on the supply are handled by Q1, D9 and D11 as described above.

## Pinouts

### J1 (USB-C to the comma device)

| Pin | USB-C name | Signal | Use |
| --- | --- | --- | --- |
| A4, A9, B4, B9 | VBUS | `12V_PROT` | 12 V supply to the device |
| A1, A12, B1, B12, shell | GND | GND | |
| A2 / A3 | TX1+ / TX1- | `ADAS_CAN_H_C` / `ADAS_CAN_L_C` | Car side of the intercepted ADAS CAN, live when the relay is energized |
| B2 / B3 | TX2+ / TX2- | `ADAS_CAN_H_MOD` / `ADAS_CAN_L_MOD` | ECU side of the intercepted ADAS CAN |
| A11 / A10 | RX2+ / RX2- | `MRR_CAN_H` / `MRR_CAN_L` | Listen-only tap on the mid-range radar CAN |
| B11 / B10 | RX1+ / RX1- | `COMMA_P` / `COMMA_N` | Wired only to J1. Reserved |
| A8 | SBU1 | `SBU 1` | Switch control input |
| A5, B5, A6, A7, B6, B7, B8 | CC, D+/D-, SBU2 | | Not connected |

### J3 ↔ J4 (CON1 section A, 20-way)

| Pin | Signal | Path |
| --- | --- | --- |
| 1 | VBAT (`Harness_12v`) | Straight through, and powers the board through F1 and Q1 |
| 6 | `USS2_PWR` | Straight through |
| 7 | `USS1_PWR` | Straight through |
| 14 | GND | Straight through, and board ground |
| 15 | `USS1_PWR_N` | Straight through |
| 16 | `USS1_Signal` | Straight through |
| 17 | `USS2_Signal` | Straight through |
| 18 | `USS2_PWR_N` | Straight through |
| 19 / 20 | ADAS CAN L / H | Intercepted through K1. `ADAS_CAN` on J3, `ADAS_CAN_MOD` on J4 |

### J5 ↔ J6 (CON1 section B, 16-way)

| Pin | Signal | Path |
| --- | --- | --- |
| 1 / 9 | MRR CAN L / H | Straight through, tapped to J1 A10/A11 |
| 2 / 3 | CMRR FR CAN H / L | Straight through |
| 4 / 5 | CMRR RR CAN H / L | Straight through |
| 10 / 11 | CMRR FL CAN H / L | Straight through |
| 12 / 13 | CMRR RL CAN H / L | Straight through |
| 15 / 16 | DMS LED1 L / H | Straight through |

## Board construction

| Layer | Use |
| --- | --- |
| F.Cu | Signals, GND pour |
| In1.Cu | Solid GND plane |
| In2.Cu | Solid GND plane, with a `12V_PROT` island under J1, C1 and D9 to D11 and a 0.3 mm `VIN` link from R5 to K1 |
| B.Cu | Signals, GND pour |

The two header pairs face out of opposite edges, so the J5↔J6 pin order is reversed. Those 12 nets cross over in the strip between the headers. The six ultrasonic lines run on B.Cu around J4. Signal tracks are 0.25 mm with 45° bends. The DMS LED drive is 0.6 mm, necked to 0.35 mm where it threads between connector pins and past two CAN vias. The VBAT passthrough leaves J3 on B.Cu at 1.6 mm (squeezed between the J3 mounting peg and the board edge), runs up the right side and across the top at 2.4 mm, and drops to F.Cu through six 0.4 mm vias for the last 2.0 mm run into J4. F1, Q1, D15 and R7 all sit in the gap between J5 and J3, in that order along the strip, and F1 is fed from that trunk through three vias. `VBAT_FUSED` is just the 6 mm hop from F1 to Q1's drain pads, so almost nothing on the board is upstream of the reverse-polarity FET. `12V_PROT` leaves Q1's source pads, drops below J3 and runs the length of the right edge on a 1.2 mm F.Cu track, across the bottom, and up through the slot where D10 used to be to reach D11, D9, C1 and R5. From C1 it continues through the In2 island, which connects solid to the VBUS pins. `VIN` gets from R5 to K1 on a 0.3 mm In2 track, because both outer layers are crossed by other traces there.

## Repository layout

| Path | Contents |
| --- | --- |
| `PCB Files/` | KiCad 10 project (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`) and design reviews |
| `images/` | Iso render |
| `3D models/` | STEP model. Still shows the rev 1 layout |

## Revision history

| Rev | Date | Changes |
| --- | --- | --- |
| 2 | November 2026 | Added the DG419 supply clamp (D12, R6, D13, C3); U1/U2 V+ and VL now come from it. Added F1 on the VBAT tap, moved D1 to the `_C` pair, added D14 on `SBU 1`, widened the ECU VBAT passthrough, and put a "12V, COMMA ONLY" note on the back silkscreen under J1. Board shrunk from 115.75 × 75.25 mm to 89.0 × 72.2 mm with every part on top. M3 holes moved into the header gaps. Re-routed, silkscreen redone. Late in the revision, **D10 (SS34, later MBRA340T3G) was replaced by Q1 + R7 + D15** — a P-channel ideal-diode pass FET — which cut the reverse-polarity element's dissipation from 1.5 W to 0.1 W at the fuse limit. The group moved into the J5↔J3 gap beside F1, so `12V_PROT` rather than `VBAT_FUSED` now makes the long run down the right edge. Before fabrication, In2 became a ground plane, copper was pulled back to 0.5 mm from the board edge, the DMS LED drive was widened, and every part got an MPN and LCSC code |
| 1 | October 2026 | First layout. Reviewed in [`PCB Files/design_review_2026-10-13.md`](PCB%20Files/design_review_2026-10-13.md) |

The rev 2 layout is reviewed in [`PCB Files/design_review_2026-11-08.md`](PCB%20Files/design_review_2026-11-08.md), and the pre-fabrication pass in [`PCB Files/design_review_2026-11-08_prefab.md`](PCB%20Files/design_review_2026-11-08_prefab.md).

## Before you build

1. Open the project in KiCad 10, refill the zones (B), and run DRC with schematic parity. It should come up with zero errors and zero unconnected items.
2. J1's row-B pads are 0.65 mm copper on a 0.45 mm drill — a 0.10 mm annular ring. This is **identical to the Volvo/Polestar harness box**, which has been manufactured and confirmed working, so it is a proven geometry rather than a blocker. JAE's own recommended pattern (drawing SJ116123) calls for a Ø0.4 drill in the same Ø0.65 pad, which would give a 0.125 mm ring and put it inside IPC-6012 Class 2; tightening the drill to 0.40 mm is a free improvement if you want it, but it is a departure from the proven board.
3. Every part has an MPN and an LCSC code. Q1 is the DMP4015SSS-13 (C508210), because the AEC-Q101 DMP4015SSSQ-13 (C531172) had no stock; they share a pinout, ratings and footprint. C2/C3 are Samsung CL10B104KB8NNNC (C1591), a JLCPCB Basic part. When checked on 8 Nov 2026, J5/J6 (34691-0162, C585844) had no LCSC stock.
4. The custom libraries (`My_Components`, `Footprints`, and the two date-named ones) are not registered — there is no `fp-lib-table` or `sym-lib-table` in the project or in your KiCad config, which is what the ERC library warnings are about. Register them before editing footprints.
5. F1 and D14 were added outside KiCad. Run Tools > Update Footprints from Library on those two to pull the exact library copies, then refill and re-run DRC. Leave J1 out of that update unless the library copy has the boss-2 slot, which only the board's own copy of J1 has.
6. Check the Molex pin numbering and polarization against the Fisker CON1 keying before installing in a vehicle. That can't be settled from the design files alone.
7. Copper is held 0.5 mm back from the board edge. `Ocean Harness.kicad_dru` allows 0.2 mm on the outer layers only around J1's boss slot, where JAE's pattern needs it, so keep the board-wide rule at 0.5 mm.
8. The board gives the comma device no ignition line (SBU2 is unconnected), so the device has to take ignition from CAN. Upstream panda firmware has no Fisker entry for that yet.

## License

Licensed under the [CERN Open Hardware Licence Version 2 - Strongly Reciprocal](LICENSE) (CERN-OHL-S-2.0).

## Disclaimer

This is a community hardware design shared as-is, with no warranty. It's designed for the Fisker Ocean only, and using it on other platforms is unverified. **Use at your own risk.**
