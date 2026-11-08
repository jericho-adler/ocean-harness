# Ocean Harness — pre-fab review (second pass), 8 Nov 2026

Reviewed `Ocean Harness.kicad_sch` / `.kicad_pcb` / `.kicad_pro` at commit `1758324` (working tree clean).
This pass was done independently of the earlier 8 Nov review: every pin, polarity and footprint was
re-derived from the raw files and checked against manufacturer data rather than carried over.

> **Applied, 8 Nov.** Findings 2–5 are fixed on the board. Finding 1 is settled in firmware: the comma
> device takes ignition from CAN, so SBU2 stays unconnected. After the changes DRC shows 0 errors and
> 0 unconnected on both stored and refilled fills, ERC 0 errors, 8 parity items, and the Gerbers are
> complete. See "Applied changes" at the end.

## Verdict

**The board is built correctly.** I found no wiring, pinout, polarity or footprint error. KiCad DRC is
clean (0 errors, 0 unconnected, stored fills current), every IC, diode, connector and the relay match their
datasheets, and a fresh Gerber export is complete and aligned.

Two things should be settled before ordering, one functional and one fabrication:

| # | Priority | Issue | Fix |
|---|---|---|---|
| 1 | **Decide before ordering** | Nothing gives the comma device an ignition signal. With stock panda firmware it never goes onroad, so it never drives `SBU 1` and the board never leaves listen mode | Fisker CAN ignition in firmware, or pull SBU2 low. A DNP 1 kΩ footprint is the cheap hedge |
| 2 | **Fix before ordering** | Every copper pour on all four layers, inner planes included, is 0.20 mm from the board edge. JLCPCB and PCBWay want ≥ 0.3 mm | Board rule back to 0.5 mm plus a J1-only custom rule. Tested: DRC stays at 0 errors |
| 3 | Should fix | D15 and R7 have no MPN; D15, R7, Q1 and R6 have no LCSC code; J5/J6's C585844 did not resolve | Fill in before generating the BOM |
| 4 | Should fix | In2 is a VIN plane (a 13 mA net), so B.Cu signals have no ground reference | Retarget In2 to GND. Needs one short VIN trace |
| 5 | Cheap insurance | The DMS LED drive passes through on 0.25 mm traces | Widen to ≥ 0.6 mm |

After that, the vehicle-side checks in section 4. No design file can answer those.

---

## 1. No ignition signal reaches the comma device

J1.B8 (`SBU2`) is unconnected. The Polestar box drives that line low through its Q1 and R7 (1 kΩ)
whenever the car's IGN is on. Fisker CON1 has no ignition pin, so this board dropped the circuit.

Panda firmware (`commaai/panda` `board/drivers/harness.h` and `board/main.c`, read 8 Nov) decides
ignition in one place:

```c
bool started = harness_check_ignition() || ignition_can;
```

- `harness_check_ignition()` returns `!get_gpio_input(<ign SBU pin>)`. Ignition means the harness ign line
  is pulled low, and nothing else counts. A floating SBU2 reads as ignition-off: the stock harness's ign
  line is open-drain, so the panda has to pull it up.
- `ignition_can` is set only by `opendbc/safety/ignition.h`, which recognises GM (0x1F1), Rivian (0x152),
  Tesla (0x221), Mazda (0x9E), VW MEB (0x3C0) and PSA (0x432). There is no Fisker entry in panda or opendbc,
  and no panda tree or Fisker code in `~/Documents/StarPilot-work`.
- Only the car safety modes call `set_intercept_relay(true, …)`. `SILENT`, `NOOUTPUT` and `ELM327` release
  it, and openpilot only selects a car safety mode once `started` is true.

With stock firmware the device boots, detects the harness (SBU1's 240 Ω reads low) and sits offroad.
`SBU 1` is never driven, U1/U2 stay bridged, and the board acts as a passthrough with a listener attached.
`bootkick` (wake on ignition) never fires either.

The October review said that if pin 1 is switched, "VBUS presence is itself the ignition signal". That does
not match this code: VBUS powers the device but is not an input to `started`.

Which fix is right depends on whether CON1 pin 1 is switched. That question has been open since October.

| Pin 1 | Fix |
|---|---|
| Switched with the car | Pull SBU2 to GND through 1 kΩ, the Polestar's R7 value. It keeps SBU2 above SBU1's 240 Ω, so orientation detection still picks the right line. The device then sees ignition whenever the board is powered |
| Constant battery | Leave SBU2 open and add a Fisker `ignition_can` entry in firmware. A hardware pull-down here would keep the device "on" permanently |

The cheap hedge for either case is a **DNP 1 kΩ 0603 from J1.B8 to GND**. Fit it if pin 1 turns out to be
switched, and leave it off if you go the firmware route.

*Basis: panda/opendbc source; raw netlist (`unconnected-(J1-PadB8)`); Polestar netlist (`SBU 2` → R7 1 kΩ
→ Q1 drain).*

## 2. Copper is 0.20 mm from the board edge, on every layer

Commit `1758324` relaxed `min_copper_edge_clearance` from 0.5 to 0.2 mm board-wide so J1's pad A12 could sit
beside the new boss-2 slot. Zone fills follow that rule, so on refill **every pour moved out to 0.2 mm**:
the GND pours on F.Cu, In1.Cu and B.Cu, and the VIN plane on In2.Cu, all the way around the outline. The
earlier review assumed only the slot was affected. Measured with a DRC run at a 0.5 mm probe rule:

| Item | Distance | To |
|---|---|---|
| GND pours (F.Cu, In1.Cu, B.Cu), VIN plane (In2.Cu) | 0.2005 mm | Board outline |
| J1 pad A12 (GND), F.Cu | 0.210 mm | J1 slot |
| `12V_PROT` island, In2.Cu | 0.236 mm | J1 slot |
| A12→B1 GND stitch, F.Cu | 0.323 mm | J1 slot |

JLCPCB and PCBWay both ask for at least 0.3 mm (0.5 mm recommended). At 0.2 mm, routing tolerance can expose
the inner planes along the edge, or the fab will hold the order to pull copper back.

**Fix, tested on a copy.** Set `min_copper_edge_clearance` back to 0.5 mm in Board Setup, and add
`PCB Files/Ocean Harness.kicad_dru`:

```
(version 1)
# JAE's DX07 pattern puts J1's own GND copper ~0.21 mm from the boss-2 slot.
# Allow that on the outer layers only; everything else keeps the 0.5 mm board rule.
(rule "J1 boss slot"
  (layer outer)
  (constraint edge_clearance (min 0.2mm))
  (condition "A.memberOfFootprint('J1') || B.memberOfFootprint('J1')"))
```

After refill, DRC gives 0 errors and 0 unconnected, with the same 43 cosmetic warnings and 9 benign parity
items as now. The pours pull back to 0.5 mm, the In2 `12V_PROT` island ends up 0.5 mm from the slot, and
J1's own outer-layer GND copper keeps the 0.2 mm that JAE's pattern forces.

*Basis: kicad-cli DRC on the original and on a fixed copy.*

## 3. Should fix

**BOM.** Every other LCSC code resolves to its exact MPN and package (15 of 16 checked).

| Ref | MPN | LCSC |
|---|---|---|
| D15 | missing (BZT52C16-7-F would match D13) | missing |
| R7 | missing (the footprint name says ESR03EZPJ104) | missing |
| Q1 | DMP4015SSSQ-13 | missing |
| R6 | ESR03EZPJ332 | missing |
| J5, J6 | 34691-0162 | C585844 did not resolve on LCSC's search or product API. Confirm before ordering |

**In2 as a ground plane.** In2 is a VIN pour over 82 % of the layer. VIN feeds the relay coil, about 13 mA.
B.Cu (158 of 365 segments) sits 0.21 mm from In2, so those signals reference a power island instead of
ground. This is the source of EMC findings SU-001, GP-001 ×28 and RP-001 ×19. It won't stop the board
working, but it is easy to fix. I retargeted the In2 VIN zone to GND on a copy, keeping the `12V_PROT`
island at priority 1. DRC reported 0 errors and exactly one unconnected item: the VIN via at (133.14, 85.30)
beside R5, which currently reaches the rest of VIN only through the plane. One short 0.5 mm VIN trace from
that via to the R5–C2 track closes it.

**DMS LED passthrough.** `DMS_LED1_H` and `DMS_LED1_L` are 0.25 mm traces of about 42 mm with one via
each. If this is the driver-monitoring IR illuminator drive, it is pulsed at amps. At 3 A peak that is
roughly 0.5 V round-trip drop; thermally it is fine at typical duty. The current isn't known, so widen them
to at least 0.6 mm. The ultrasonic supplies (0.25 mm, 60–71 mm) are fine at sensor currents.

**Assembly polarity.** D15's cathode mark is only on F.Fab, because on silk it landed on Q1. Fabs use
different SOD-123 and SOT-23 rotation conventions, so check every polarised part (D1–D3, D8, D9, D11–D15,
CR1, Q1, U1, U2) in the assembler's placement preview. Pad 1 is the cathode on every diode footprint here.

**J1 library copy.** The boss-2 slot exists only in the board's embedded J1. If you register the libraries
and run *Update Footprints from Library* on J1 against a copy without the slot, the slot disappears with no
warning. Update the library footprint first, or leave J1 out of that update.

**Minor.**
- No test points. Pads on `12V_PROT`, `VIN`, `SW_VCC`, `SBU 1` and GND would help bring-up.
- U2's V+ is 8.2 mm from C3 (U1's is 2.4 mm). A second 100 nF at U2 is cheap.
- The R2, R4, D14 and D11 designators overlap on silk.
- D1 is 0.37 mm from the bottom edge, so keep any panel rail off that edge.
- The 0.6 mm × 1.6 mm F1 feed is short enough not to matter. Widening it is optional.
- The README still says the STEP model shows rev 1, but it was regenerated from rev 2 in `d0ea9db`.

## 4. Before installing in the car

These can't be settled from the design files.

1. **Connector keying.** Molex's Stac64 catalogue (p.10) lists 34691-0200 as the 20-way, polarisation A,
   black, and 34691-0162 as the 16-way, polarisation C, brown. The car's CON1 plugs must be a black 20-way and
   a brown 16-way (mating 34729-0200 and 34729-0162) or they won't seat. The footprint numbers row-wise:
   pins 1–10 on the inboard row and 11–20 on the edge row. I couldn't get drawing SD-34691 to confirm that,
   so check it against a real header.
2. **Every populated cavity is carried.** Fourteen cavities are left open: J3/J4 2–5 and 8–13, J5/J6 6–8
   and 14. Look at the back of the car's plugs. A wire in any of those cavities would be cut off from the ECU.
3. **Pin 1 switched or constant.** This decides finding 1. If pin 1 is constant battery, the board alone
   draws about 12 mA around the clock (about 0.3 Ah/day), plus the comma device while it is up.
4. **Shared fuse and wires.** The comma device's current and its return now run through the ECU's own pin 1
   and pin 14 wires and the ECU's fuse. Check that fuse against ECU plus comma peak current. Your October
   notes say pin 14 is a secondary ground, so check its gauge too.
5. **Where the terminations are.** With the car off, measure ADAS CAN H–L at the harness plug and at the
   ECU. If the ECU holds one of the two 120 Ω terminators, intercept mode leaves the car-side segment
   single-terminated, since R4 only terminates the ECU side. That is fine at 500 kbit/s over short runs, and
   worth knowing if the bus is CAN FD.
6. **H/L assignment.** Pins 20/19 (ADAS) and 9/1 (MRR) are taken as H/L. A swap would not hurt the car,
   because the passthrough and the bridge are symmetric, but the comma device would read garbage on that bus.

## 5. First power-on checks

- **SBU 1 high level.** Panda drives its relay lines from open-drain, active-low GPIOs into external
  hardware. The code doesn't say what voltage lands on SBU. It does switch the SBU sense pins out of ADC mode
  because they are "not 5V tolerant in ADC mode", which points to about 5 V. At 5 V, R2+R3 draw 21 mA and
  each dissipates 52 mW against the ESR03's 0.25 W. Above about 10 V they would be over their rating, so
  scope it once. The circuit is identical on the Polestar box, so you can check R2/R3 there first.
- **DG419 threshold.** VL is tied to V+ ≈ 12 V. At that supply the datasheet's typical switching point is
  V_INH ≈ 2.6 V and V_INL ≈ 2.25 V (Vishay 76432, p.10). The guaranteed 2.4 / 0.8 V figures only hold at
  VL = 5 V. That is fine for a 5 V drive and thin for 3.3 V into 240 Ω.
- **Relay pull-in vs temperature.** Must-operate is 9.0 V at a 23 °C coil, and coil resistance rises
  0.39 %/°C. Through R5 that needs `12V_PROT` of at least 10.5 V at 23 °C, 12.2 V at 70 °C and 12.7 V at
  85 °C. A running EV's 13.5–14.5 V covers it. At a resting 12.4 V in a hot car the relay may not pull in,
  which fails safe to passthrough.
- **Diagnostics.** If U1/U2 don't switch when intercepting, openpilot reports a relay malfunction because
  it sees the ECU's messages on the car bus. That makes a good first functional test.

## 6. Verified correct

| What | Result | Basis |
|---|---|---|
| Schematic ↔ PCB | 0 unconnected and 0 DRC errors. 9 parity items: five mechanical footprints and four field-text drifts. Identical after refill, so the stored fills are current. No DRC/ERC exclusions | kicad-cli |
| ERC | 0 errors. The 107 warnings are pin-type, off-grid and unregistered-library | kicad-cli |
| Diode polarity (12 parts) | Pin 1 is graphically the cathode in the custom SMAJ16A and 1N4148W-7-F symbols and is K in `Device:D_*`; footprint pad 1 carries the cathode mark. TVS cathodes are on `12V_PROT`, CR1's cathode is on VIN, D12 conducts VIN→SW_IN, and both zeners have the cathode on the higher rail | Raw files |
| Q1 DMP4015SSSQ | Pins 1–3 S, 4 G, 5–8 D (p.1) match the footprint nets. Drain is on the input, source on the output, and D15's cathode is on the source. V_GSS is ±25 V, so D15 is needed. 11 mΩ gives 0.1 W at 3 A | Datasheet |
| U1/U2 DG419LE | Pinout 1 COM, 2 NC, 3 GND, 4 V+, 5 VL, 6 IN, 7 V−, 8 NO, and logic 0 = NC on (p.1). Supply range 3–16 V against SW_VCC ≈ 11–12 V. R_on 11 Ω typ, 18 Ω max over temperature (p.3) | Datasheet |
| K1 G5V-2-H1 | COM 4/13, NC 6/11, NO 8/9, coil 1–16, no coil polarity (p.4), so unpowered hard-wires the car to the ECU. Hole pattern (1.0 mm on 7.62/5.08/5.08, rows 7.62 mm) matches the footprint. 960 Ω coil, 9.0 V must-operate, 21.6 V max (p.2) | Datasheet |
| D1–D3, D8 PESD1CAN | Pins 1/2 are the line cathodes and 3 is common (Table 2); the lines are on 1/2 and GND on 3 | Datasheet |
| J1 DX07S024XJ1R1100 | All 24 contacts within 0.000 mm of JAE SJ116123 detail A, numbering not mirrored. Pin functions match JAE Table 2. Pinout matches the Polestar box role for role: car on TX1 A2/A3, ECU on TX2 B2/B3, MRR on RX2 A11/A10, SBU1 as control | Drawing + raw file |
| J3↔J4, J5↔J6 | Every carried pin lands on the same number on both sides. Only 19/20 differ, and they are the intercepted pair | Netlist |
| CAN H/L | H stays H and L stays L through K1, U1/U2 and J1, with + on H | Netlist |
| F1 | 0685T3000-01 is a 1206 slow-blow fuse, 3 A, 63 V, 50 A breaking capacity. Matches its footprint | Distributor data |
| Power copper | VBAT trunk 2.4 mm (≈ 4.5 A at 10 °C rise), narrowest section 1.6 mm (≈ 3.4 A). `12V_PROT` is 1.2 mm with four 0.3 mm vias into the In2 island. Six 0.4 mm vias at the VBAT layer change | Raw file, IPC-2221 |
| `12V_PROT` continuity | Traced by hand from Q1 to D11, C1, the In2 island and J1 VBUS | Raw file |
| Gerbers | All 11 layers plus PTH/NPTH drill, aligned, 89.0 × 72.2 mm | analyze_gerbers |
| Stac64 rating | 10 A per circuit | Molex catalogue |

## 7. Environmental limits

| Part | Rated ambient |
|---|---|
| K1 G5V-2-H1 | −25 to +70 °C, and 10 g shock before contacts malfunction |
| J1 DX07 | −30 to +80 °C |
| U1/U2 DG419LE | −40 to +85 °C |
| Everything else | −55 °C or wider |

K1 is the limit. In-cabin locations can exceed 70 °C on a hot soak. It fails safe, but expect it to be the
first part to age. Omron (p.4) also warns that contacts left energised for long periods can develop films.

## 8. False positives and reviewer overrides

- **Analyzer "islands" on 7 nets** (`12V_PROT`, `VBAT_FUSED`, `Harness_12v`, `SW_VCC`, `SBU 1`,
  `ADAS_CAN_H_C`, `ADAS_CAN_L_C`). The analyzer's union-find doesn't treat T-junctions or tracks passing
  through pads as connected. For example, `VBAT_FUSED` is one 1.2 mm bar through the centres of Q1 pads 5–8.
  KiCad's own connectivity reports 0 unconnected, and `12V_PROT` was traced by hand.
- **PP-001 ×2**: U1/U2 V+ reaches VIN through the D12 Schottky, a path the analyzer's 2-hop search can't
  cross. **RS-001** is PWR_FLAG hygiene.
- **GR-004**: the paste count is short by exactly the 96 THT pads, 65 vias and 3 fiducials, as expected.
- **ES-001**: D3 protects J3 pins 19/20 (7.3 mm away), not J5.
- **PM-002**: the connector overhangs are intentional for edge-mount housings.
- **EMC GP-001, SU-001 and RP-001** are real but EMC-only. See "In2 as a ground plane" above.

## 9. Changes since the earlier 8 Nov review

| Earlier item | Now |
|---|---|
| 1 Schematic/PCB desync | Resolved, confirmed |
| 2 J1 annular ring | Agree. It puts the board on the advanced fab tier, like the Polestar |
| 3 BOM gaps | Still open, and C585844 is added to the list |
| 4 Libraries not registered | Still open. See the J1 library caution |
| 5 B.Cu over a split plane | Still open. The fix is now known to cost one trace |
| 6 ESD on the CMRR/DMS pairs | Downgraded. Those are passthroughs between OEM parts with their own protection, and adding 11–17 pF per line to CAN FD isn't free |
| 7 R4 termination value | Still open, low priority |
| "Move one SMAJ16A next to Q1" | Careful. A unidirectional TVS on `VBAT_FUSED` conducts under reverse polarity and blows F1. Use a bidirectional part if you want input clamping. Q1 is avalanche-rated (E_AS 242 mJ), and the ECU's own input protection shares the line |

New in this pass: finding 1 (re-raised from October, with the panda code), finding 2, the DMS LED width, the
LCSC check, temperature ratings, and the J1 library caution.

## 10. What was run

- `analyze_schematic.py`, `analyze_pcb.py --full --proximity`, `cross_analysis.py` (0 findings),
  `analyze_emc.py` (62 findings, all ground-reference related), `analyze_thermal.py` (nothing to assess,
  since the board has no regulator; dissipation is hand-computed above), SPICE with ngspice-42 and PCB
  parasitics (6/6 pass on the R2/R3 arithmetic and decoupling), and `analyze_gerbers.py` on a fresh export.
- kicad-cli ERC; DRC with schematic parity on stored and refilled fills; DRC with exclusions (none); a
  0.5 mm edge probe; and both fixes tested on copies. Your project files were not modified.
- Datasheets extracted from the board's embedded files: DG41xLE, G5V-2, PESD1CAN, JAE SJ116123 and Rohm ESR.
  Fetched separately: DMP4015SSSQ, the Molex Stac64 catalogue, and the panda and opendbc source.
- **Not done.** No lifecycle audit, because no distributor API keys are set. No Molex SD-34691 drawing for
  the circuit numbering, because it couldn't be retrieved. SMAJ16A, BZT52, DSK14 and 1N4148W were checked
  against LCSC parametric data, not manufacturer PDFs; all are standard parts. The untracked enclosure CAD
  was not reviewed. The vehicle-side pinout can't be checked from these files.

## Ordering notes

- 4 layers, 1.62 mm, 1 oz copper on all layers.
- Advanced tier, because of the 0.10 mm annular rings on J1 row B and the vias. This matches the Polestar.
- The stackup doesn't set a surface finish. ENIG suits J1's 0.5 mm-pitch SMD row best.
- PCBWay's minimum NPTH is 0.8 mm, and J1's bosses are 0.775 mm. JLCPCB's minimum is 0.5 mm.
- J1 is a hybrid part: row A reflows, while row B and the shell legs need hand or selective soldering.
  J3–J6 and K1 are through-hole.

## Applied changes, 8 Nov 2026

| Finding | Change |
|---|---|
| 1 Ignition | No hardware change. The comma device takes ignition from CAN, which needs a Fisker entry in panda/opendbc `ignition_can` |
| 2 Edge clearance | `min_copper_edge_clearance` is back to 0.5 mm. A new `Ocean Harness.kicad_dru` allows 0.2 mm only for J1's outer-layer copper at its slot. Pours refilled |
| 3 BOM | See the table below. R6 moved to the 1 % ESR03EZPF3301, because the 5 % ESR03EZPJ332 (C2073850) had no stock; it is the same family, footprint and rating. R6's schematic Description named a nonexistent D16 and now matches the board's text |
| 4 In2 | The VIN pour is retargeted to GND and the layer is typed `power`, like In1. The `12V_PROT` island keeps priority 1. VIN reaches K1.16 from R5's via on a 0.3 mm In2 track: north to y 83.9, east to x 134.9, north to y 71.5, then west to K1.16 |
| 5 DMS LED | 0.6 mm on the open runs and 0.35 mm through the J5/J6 pin escapes and past the CMRR_FR/FL_CAN_H vias, with 0.5 mm at the DMS_H via and 0.25 mm on one 1.1 mm jog. About 75 % of each run is now 0.6 mm, which roughly halves the resistance (≈ 167 → 82 mΩ round trip) |

| Ref | MPN | LCSC | LCSC stock on 8 Nov |
|---|---|---|---|
| Q1 | DMP4015SSS-13 | C508210 | 2,539. Replaces the AEC-Q101 DMP4015SSSQ-13 (C531172), which had 0; same pinout, ratings and footprint |
| C2, C3 | CL10B104KB8NNNC (Samsung) | C1591 | JLCPCB Basic part; replaces C14663, which JLCPCB showed as unavailable |
| R6 | ESR03EZPF3301 | C510091 | 4,060 |
| R7 | ESR03EZPJ104 | C253331 | 9,850 |
| D15 | BZT52C16-7-F | C397929 | 3,560 |
| J5, J6 | 34691-0162 | C585844, confirmed as the right part | 0 |

**Verification after the changes.**
- DRC: 0 errors, 0 unconnected, and the same 43 cosmetic and library warnings, identical with stored and
  refilled fills. Parity has 8 items: the five mechanical footprints and the C3, D12 and D13 text drifts.
- ERC: 0 errors.
- Gerbers complete and aligned.
- A KiCad BOM export has 21 lines covering 30 parts, all with an MPN and an LCSC code.
- The EMC analyzer score went from 53.5 to 65.5, with SU-001 and SU-002 cleared. GP-001 is unchanged
  because it counts any copper as a reference, VIN included; its remaining hits are the connector pin fields.
