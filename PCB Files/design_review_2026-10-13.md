# Design Review — Ocean Harness (production readiness)

**Date:** 2026-10-13 | **Run:** `analysis/2026-10-12_1741-2/` | **KiCad:** 10.0.7 (board v20260306)
**Board:** 115.75 × 75.25 mm, 4-layer, 22 schematic components / 24 footprints, 69 nets, single sheet
**Scope:** will it function, and is it ready to fabricate — reviewed against the Fisker CON1 pinout table
and against the confirmed-working Polestar reference design
(`/home/jericho/Documents/_Passthrough_HarnessBox_Final.kicad_pro/`).

**Analyzers run:** `analyze_schematic.py`, `analyze_pcb.py --full`, `cross_analysis.py`,
`analyze_emc.py`, `analyze_thermal.py`, plus `kicad-cli pcb drc` (with and without `--refill-zones`,
`--schematic-parity`) on **both** this board and the reference board.

---

## Verdict

**The board will function.** The active circuit is a pin-for-pin port of the proven Polestar design, and
all 36 CON1 positions map correctly onto the Fisker pinout you supplied. I found no electrical defect
that requires rerouting.

**It is not yet ready to send to fab**, but everything blocking it is a file/BOM/silkscreen fix, not a
layout change. The most important one is that **the committed board has stale zone fills** — exported
as-is, the USB-C shield is left floating.

| | |
|---|---|
| Functional correctness | **Pass** — verified against pinout, reference design and datasheets |
| KiCad DRC (zones refilled) | **Pass** — 0 errors, 0 unconnected, parity clean |
| Ready to fabricate today | **Yes, once you assign 3 passive MPNs** — the 5 blockers below were fixed on 2026-10-13 |

---

## Fixes applied — 2026-10-13, branch `fix/production-blockers`

All five blockers were addressed in-tree. **No track, pad, footprint position or net was
modified**: net membership is byte-for-byte identical across all 70 nets, all 24 original
footprints have unchanged pad-to-net maps, and ERC is unchanged at 76 warnings / 0 errors.

| # | Blocker | Status | What changed |
|---|---|---|---|
| 1 | Stale zone fills | **Fixed** | Zones refilled and the board re-saved. DRC now reports **0 unconnected** — all four J1 shield pads are tied into the GND pour |
| 2 | No MPNs | **Mostly fixed** | `MPN`, `Manufacturer` and `Spec` fields added to 22 symbols and mirrored onto the PCB footprints. Coverage 0/13 → **10/13 (77 %)**; `SS-001` (blocker) is now `SS-002` (warning) |
| 3 | D9/D11 no polarity mark | **Fixed** | Cathode bar added on F.SilkS and F.Fab to both parts |
| 4 | No fiducials | **Fixed** | FID1–FID3 added on F.Cu; `FD-001` cleared |
| 5 | 0.1 mm annular ring | **Mostly fixed** | 25 of 27 vias grown 0.5 → 0.6 mm (ring 0.15 mm, meets IPC Class 2). **2 vias cannot grow** — see below |

**Verification after the fixes** (`kicad-cli pcb drc --refill-zones --schematic-parity`):

```
57 violations, 0 errors, 0 unconnected items
   lib_footprint_issues 17 | silk_over_copper 17 | silk_edge_clearance 12 | silk_overlap 11
5 schematic parity issues -- all "Extra footprint": H1, H2, FID1, FID2, FID3 (no schematic symbol, by design)
```

That is **exactly the original warning profile** — the fixes introduced no new warnings. EMC risk
is unchanged at 34.0, routing still complete, 70/70 nets intact.

### What is deliberately still open

- **Three jellybean passives have no MPN** — C1 (0.33 µF 0603), C2 (0.1 µF 0603), R5 (160 Ω 0805).
  Their full electrical spec is now recorded in the new `Spec` field on each symbol, so the BOM is
  unambiguous, but the actual supplier part is your call (house stock / preferred vendor). Assign
  these and `SS-002` clears too.
- **Two vias keep the 0.1 mm ring.** The vias at (145.314, 104.420) on `/COMMA_P` and
  (145.822, 102.896) on `/ADAS_CAN_L_MOD` sit in the J1 fan-out with exactly 0.200 mm to the
  neighbouring `MRR_CAN` tracks. Growing them to 0.6 mm produced real clearance **errors**
  (0.150 mm actual vs 0.200 mm required), so they were reverted to 0.5 mm. Closing these two
  requires moving a track, which is out of scope. The board still needs JLCPCB's advanced tier for
  those two holes — but the exception is now 2 vias instead of 27.
- **The Molex polarization code is still unresolved.** Each connector's `Spec` field now carries an
  explicit *"VERIFY polarization code against Fisker CON1 keying"* note, but this cannot be settled
  from the design files. See "Confirm before installing", item 1.
- **The `My_Components` library still has the original defects.** The cathode bars were added to the
  D9/D11 *board instances*, because the library is not in this checkout's library table. The library
  footprint — and the J1 peg-hole defect the previous review describes — will reproduce the problem
  in the next project unless fixed at the library.

### Implementation notes

- D9 and D11 received the cathode bar in **different positions**, because their surroundings differ:
  D9's left side carries the incoming `12V_PROT` feed, so its bar sits *below* the body
  (0.70 mm clearance); D11's sits to the *left* at x = −3.55 (0.33 mm clearance). Both mark the
  pin-1 / cathode end, and both carry an identical F.Fab bar so the assembly drawing is consistent.
- Fiducials are at (121.25, 89.25), (129.75, 44.75) and (160.75, 97.75) — a scalene, non-symmetric
  triangle inside the open middle band of the board. They are deliberately **not** near the board
  corners: J4/J6 and J3/J5 housings cover the outer thirds of the top surface, so corner fiducials
  would sit under a connector body. Standard KiCad `Fiducial_1mm_Mask2mm` geometry (1 mm copper,
  2 mm mask opening, 0.6 mm zone keepback), `exclude_from_bom` and `exclude_from_pos_files`.
- Helper scripts used for the clearance maths are in `analysis/helpers/`; the verification DRC/ERC
  reports are in `analysis/verify/`.

---

## Critical findings

### 1. Zone fills in the committed board are stale — refill before exporting gerbers
**Raw-file verified / DRC-verified.** Severity: **blocker (trivial fix)** — **FIXED 2026-10-13**

DRC on the file exactly as committed:

```
Found 3 unconnected items
  - Zone [GND] on F.Cu and In1.Cu  <->  PTH pad S1 [GND] of J1 @ (137.256, 110.79)
  - PTH pad S1 [GND] of J1 @ (146.456, 107.79)  <->  Zone [GND] on B.Cu
  - PTH pad S1 [GND] of J1 @ (146.456, 107.79)  <->  PTH pad S1 [GND] of J1 @ (146.456, 110.79)
```

All four of J1's USB-C shell pads are assigned GND in the netlist but have no copper reaching them.
This is exactly what the last commit (`22451b3`, "Tie all four J1 shell pads to GND") set out to do —
the net assignment landed, the fill did not.

Re-running the identical DRC with `--refill-zones`:

```
Found 0 unconnected items
Found 2 schematic parity issues   (H1, H2 — mounting holes, no schematic symbol, by design)
```

So it is purely a stale fill. KiCad plots zones from the stored fill data, so **gerbers exported from
the file as committed would ship an ungrounded USB-C shell** — the cable shield would have no ESD or
EMC return path at this end.

**Fix:** open the board, `Edit → Fill All Zones` (**B**), save, commit, then export. Nothing moves.

### 2. No MPNs on any BOM line — and two parts are genuinely ambiguous
**Analyzer-derived + datasheet-verified.** Severity: **blocker (sourcing)** — **FIXED 2026-10-13** (10/13; 3 jellybean passives left to assign)

`SS-001`: 0 of 13 BOM lines carry an MPN; the part numbers sit in the `Value` field instead. Two of
these are not safely orderable from the value string alone:

- **D10 "SS34"** — the board uses the `Diode_SMD:D_SMA` footprint (DO-214AC). Vishay's SS34 is
  **SMC (DO-214AB)** and will not fit ([Vishay doc 88751](https://www.vishay.com/doc/?88751=), p.1,
  "Case: SMC (DO-214AB)"). SS34 is sold in both packages depending on manufacturer — order an
  explicitly **SMA / DO-214AC** part (e.g. Diodes Inc. `SS34-13-F`).
- **J3/J4 "Molex 0346910200"** — this is the Stac64 34691 series, and the 20-circuit header ships in
  several **polarization/keying codes (A, C, D)**. The code must match the Fisker CON1 keying or the
  connector will not mate. Same applies to J5/J6 (`0346910162`).

### 3. D9/D11 footprint has no polarity marking at all
**Raw-file verified.** Severity: **blocker (assembly)** — **FIXED 2026-10-13** on the board instances; library still defective

The `My_Components:SMAJ16A` footprint draws only a plain rectangle on F.SilkS and F.Fab — no cathode
band, no pin-1 marker:

```
F.SilkS  (-2.52, 1.298)->(2.52, 1.298)      F.Fab  four lines forming a plain rectangle
F.SilkS  ( 2.52,-1.298)->(-2.52,-1.298)
```

The netlist is correct — I traced the symbol graphics and pin 1 is the cathode (Zener bar with angled
tips at the pin-1 end), and both parts have pin 1 on `12V_PROT`, pin 2 on `GND`. That is right for a
unidirectional TVS. But a reversed SMAJ16A forward-conducts at ~0.8 V and **dead-shorts the 12 V rail**,
and the assembler has nothing on the board to orient against.

For contrast, D10's footprint does carry a proper fab-layer diode symbol and a silkscreen band bracket
on the pin-1 (cathode) side.

**Fix:** add a silkscreen cathode band / pin-1 dot to the footprint. Silkscreen only.

### 4. No fiducials
**Analyzer-derived.** Severity: **blocker (assembly)** — **FIXED 2026-10-13**

`FD-001`: 0 fiducials on F.Cu with 17 SMD components, finest pad dimension 0.30 mm. Add ≥3
non-symmetric fiducials on F.Cu. Copper + mask only, no reroute.

### 5. Via annular ring below IPC Class 2
**Analyzer-derived.** Severity: **high (fab yield / cost)** — **FIXED 2026-10-13** for 25 of 27 vias

All 27 vias are 0.5 mm pad / 0.3 mm drill → **0.1 mm annular ring**, below the IPC-6012 Class 2 minimum
of 0.125 mm (`DFM-001`, `DFM-002`), and inside JLCPCB's advanced-process tier. Changing the via pad to
0.6 mm is a net-class setting plus a refill — no manual rerouting.

---

## Functional verification

### Fisker CON1 pinout — full match

Checked at the **PCB pad level** (`pad_nets`), so library footprint pad numbering is inside the check,
not just the schematic. Harness lands on J3+J5; J4+J6 continue to the ECU.

**Section A — J3/J4 (20 circuits)**

| Pin | Fisker table | Board net | |
|---|---|---|---|
| 1A | VBAT (+) | `Harness_12v` (J3.1 ↔ J4.1) | pass-through, also feeds the board |
| 2A, 3A, 4A | NOT USED | unconnected | correct |
| 5A | NOT USED (internally GND) | unconnected | correct |
| 6A | USS_PWR_B — rear USS power | `USS2_PWR` | pass-through |
| 7A | USS_PWR_A — front USS power | `USS1_PWR` | pass-through |
| 8A | NOT USED (internally GND) | unconnected | correct |
| 9A, 10A | NOT USED (ex HSCAN1_DC_N/P) | unconnected | correct — not used for Fisker |
| 11A, 12A, 13A | NOT USED | unconnected | correct |
| 14A | VBAT (−) | `GND` | tied to board ground — see note below |
| 15A | USS_GND_A — front USS gnd | `USS1_PWR_N` | pass-through |
| 16A | USS_DSI_A — front DSI3 | `USS1_Signal` | pass-through |
| 17A | USS_DSI_B — rear DSI3 | `USS2_Signal` | pass-through |
| 18A | USS_GND_B — rear USS gnd | `USS2_PWR_N` | pass-through |
| 19A | HSCAN1_N — vehicle CAN low | `ADAS_CAN_L` → relay → `ADAS_CAN_L_MOD` | **intercepted** |
| 20A | HSCAN1_P — vehicle CAN high | `ADAS_CAN_H` → relay → `ADAS_CAN_H_MOD` | **intercepted** |

**Section B — J5/J6 (16 circuits)**

| Pin | Fisker table | Board net | |
|---|---|---|---|
| 1B | HSCAN2_N — MRR low | `MRR_CAN_L` | pass-through + listen-only tap to J1.A10 |
| 2B / 3B | HSCAN3_P/N — CMRR_FR | `CMRR_FR_CAN_H` / `_L` | pass-through |
| 4B / 5B | HSCAN5_P/N — CMRR_RR | `CMRR_RR_CAN_H` / `_L` | pass-through |
| 6B | NOT USED | unconnected | correct |
| 7B / 8B | NOT USED (ex OMS_LED−/+) | unconnected | correct — not used for Fisker |
| 9B | HSCAN2_P — MRR high | `MRR_CAN_H` | pass-through + tap to J1.A11 |
| 10B / 11B | HSCAN4_P/N — CMRR_FL | `CMRR_FL_CAN_H` / `_L` | pass-through |
| 12B / 13B | HSCAN6_P/N — CMRR_RL | `CMRR_RL_CAN_H` / `_L` | pass-through |
| 14B | NOT USED | unconnected | correct |
| 15B | DMS_LED− | `DMS_LED1_L` | pass-through |
| 16B | DMS_LED+ | `DMS_LED1_H` | pass-through |

Every used pin is carried; every pin the table marks NOT USED is left unconnected; H/L and P/N polarity
is consistent end to end. **No pinout errors found.**

### Active circuit vs the proven Polestar board — identical

Mapping the reference's net names onto Fisker's (`VCU_*` = vehicle side, `CAMERA_*` = ECU side,
`*_C` = comma side), the two designs are the same circuit:

| | Reference (works) | Ocean | |
|---|---|---|---|
| K1 coil | pin 16 → VIN, pin 1 → GND | pin 16 → VIN, pin 1 → GND | same |
| K1 pole 1 | COM 4 = `VCU_N`, NC 6 = `CAMERA_N`, NO 8 = `VCU_N_C` | COM 4 = `ADAS_CAN_L`, NC 6 = `..._L_MOD`, NO 8 = `..._L_C` | same |
| K1 pole 2 | COM 13 = `VCU_P`, NC 11 = `CAMERA_P`, NO 9 = `VCU_P_C` | COM 13 = `ADAS_CAN_H`, NC 11 = `..._H_MOD`, NO 9 = `..._H_C` | same |
| U1 DG419 | COM = ECU H, NC = comma H, NO = R4 | COM = ECU H, NC = comma H, NO = R4 | same |
| U2 DG419 | COM = comma L, NC = ECU L, NO = open | COM = comma L, NC = ECU L, NO = open | same |
| R4 120 Ω | U1.NO ↔ ECU-side L | U1.NO ↔ ECU-side L | same |
| R2/R3 on SBU1 | 120 + 120 to GND, tap unused | 120 + 120 to GND, tap unused | same |
| J1 comma pinout | 24 positions + shell | identical roles | same except B8 |

The de-energised relay gives the fail-safe straight-through harness↔ECU path; energising it hands the
harness pair to comma port A while port B stays on the ECU, and the DG419s pick the final route under
`SBU 1`. The U1/U2 asymmetry (U1 switches the 120 Ω termination, U2 bridges only the L line) looks odd
in isolation but is **exactly** what the working board does.

**Only intentional difference:** J1.B8 (`SBU2`) is a no-connect here. The reference drove it low through
Q1/R6/R7/R8 when `IGN` was active; Fisker CON1 has no ignition pin, so the circuit was dropped. See
"confirm before install" below.

### Diode orientations — all correct
**Raw-file verified** from footprint fab-layer geometry and symbol graphics.

| Part | Role | Orientation | |
|---|---|---|---|
| D10 SS34 | reverse-battery protection | pad 1 = cathode (fab bar at pad-1 end) → `12V_PROT`; anode → `Harness_12v` | correct |
| CR1 1N4148W | relay coil flyback | pad 1 = cathode (fab bar at pad-1 end) → `VIN`; anode → `GND` | correct, reverse-biased in normal operation |
| D9, D11 SMAJ16A | 12 V rail clamp | pin 1 = cathode (Zener bar) → `12V_PROT`; pin 2 → `GND` | correct (but see blocker 3) |
| D1, D2, D3, D8 | PESD1CAN on CAN pairs | CATHODE_1/2 on the pair, CATHODE_COM on GND | correct |

### R5 dropper — correctly connected

Worth stating explicitly because the analyzer's connectivity graph reports it as broken and it is not.
R5 (160 Ω, 0805) sits at (126.066, 73.406) rotated 90°. Applying KiCad's screen convention (Y-down):

```
R5 pad 1 (net /12V_PROT) @ (126.066, 74.3185)  <- track net "/12V_PROT" ends here   MATCH
R5 pad 2 (net VIN)       @ (126.066, 72.4935)  <- track net "VIN"       ends here   MATCH
```

I validated the rotation convention empirically across the whole board
(`analysis/helpers/pad_net_check.py`): the Y-down convention agrees on 135/158 track endpoints vs
73/109 for the Y-up one, and the residual disagreements are all in J1's 0.5 mm-pitch pad field where
nearest-pad matching is ambiguous. KiCad's own DRC is the authority and reports no short and no
unconnected item here.

With the coil at 960 Ω, `VIN = 12V_PROT × 960/1120 = 0.857 × 12V_PROT`:

| `Harness_12v` | `12V_PROT` (−SS34) | `VIN` = coil voltage | |
|---|---|---|---|
| 14.4 V (DC-DC high) | ~14.0 V | **12.0 V** | at the coil's 12 V rating |
| 13.8 V (DC-DC low) | ~13.4 V | **11.5 V** | fine |
| 10.9 V (degraded aux) | ~10.5 V | 9.0 V | at the 75 % pick-up limit — drops out to fail-safe below this, which is benign |

Coil current 12.5 mA, R5 dissipation 25 mW in a 125 mW part. Comfortable.

### DG419 — datasheet-verified
[Vishay doc 61565 Rev. B, 21-Sep-2026](https://www.vishay.com/docs/61565/dg417.pdf), p.1:

- **Pinout** `1=D, 2=S1, 3=GND, 4=V+, 5=VL, 6=IN, 7=V−, 8=S2` — matches the board's
  `COM/NC/GND/V+/VL/IN/V−/NO` symbol exactly.
- **Truth table (DG419):** logic 0 → SW1 on (COM–NC); logic 1 → SW2 on (COM–NO).
- **Logic thresholds:** logic "0" ≤ 0.8 V, logic "1" ≥ 2.4 V.
- **Absolute max:** V+ 44 V; VL `(GND − 0.3)` to `(V+) + 0.3`; digital inputs `(V−) − 2` to `(V+) + 2`;
  30 mA continuous per terminal.
- Unipolar operation at **V+ = 12 V, V− = 0 V is an explicitly specified condition** (p.3), analog
  signal range 0–12 V, R<sub>DS(on)</sub> ~40 Ω.

The board ties VL to V+ (≈ 11.5–12.0 V), which is inside absolute max but above the datasheet's
characterised VL of 5 V. The threshold graph on p.5 plots V<sub>TH</sub> vs V+ for VL = 5 V (~1.3 V) and
VL = 7 V (~2.0 V), so the threshold does climb with VL. **This is not a regression:** the reference board
ties VL to its VIN with no dropper, so its VL runs ~2 V *higher* than Ocean's, and it works. Ocean has
strictly more logic margin than the proven design. Still worth one bench check — see below.

### Power and ground pass-through — substantially better than the reference

Computed from `--full` track geometry at 1 oz (`analysis/helpers/net_resistance.py`):

| | Reference (confirmed working) | Ocean | |
|---|---|---|---|
| ECU VBAT pass-through | 108.5 mm @ 0.20 mm = **268 mΩ** | 123.9 mm @ 1.00 mm = **61 mΩ** | 4.4× better |
| ECU ground return | `Harness_GND`, 76.9 mm @ 0.20 mm = **190 mΩ** | board GND plane ≈ **2 mΩ** | far better |
| GND copper | GND zone on F.Cu + In1.Cu + B.Cu | GND on F.Cu + In1.Cu + B.Cu | same |
| EMC risk score | 37.0 | **34.0** | marginally better |
| DRC unconnected | 0 | 0 (after refill) | same |

This settles the prior review's "Blocker 1". Two corrections to that document: the VBAT net in the
**committed** board measures 61 mΩ at a uniform 1.0 mm width, not the 24.6 mΩ / 1.95 mm the review
claims (that widening is not in any committed revision); and the ECU's VBAT budget is no longer the
open question it was, because the proven board carries the same load through **4.4× more resistance**
and works. The Molex Stac64 34691 header is listed at 10 A, so the connector is not the limit either.

`USS1/2_PWR` and `_PWR_N` run at 0.25 mm (165–181 mΩ over ~85 mm). For DSI3 sensor banks at a few
hundred mA that is a ~30 mV drop — fine, though sized by default rather than by intent.

---

## Confirm before installing in a vehicle

These cannot be settled from the design files.

1. **Connector pin numbering and keying (highest consequence).** The board's J3/J4 footprint is a
   2 × 10 through-hole field on a 2.54 mm grid, numbered 1–10 in one column and 11–20 in the other;
   J5/J6 is 2 × 8 numbered 1–8 / 9–16. Everything above assumes board pad *N* = Fisker pin *N*A/*N*B.
   I could not obtain the Molex 34691 customer drawing to confirm the cavity numbering or the
   polarization code. **Check the Molex drawing against the Fisker CON1 connector drawing, or mate a
   sample, before committing to fab.** If the numbering or keying is off, every signal shifts.
2. **Is pin 1A switched or constant battery?** `SBU2`/ignition was dropped (no Fisker ignition pin), so
   J1.B8 floats. If 1A is switched, VBUS presence is itself the ignition signal and this is fine. If it
   is constant-battery, the comma device has no reason to sleep — and on an EV a flat aux battery can
   leave the car unable to close its HV contactors.
3. **D10 thermal at the comma device's real current.** The reference had no series diode in the comma
   power path, so this is the one genuinely new stress. All comma power flows through D10
   (J1.A4/A9/B4/B9 are all on `12V_PROT`). Computed in `analysis/helpers/d10_thermal.py`, Tj max 150 °C:

   | Load | P | Tj @ 25 °C amb | Tj @ 60 °C | Tj @ 85 °C |
   |---|---|---|---|---|
   | 1.0 A | 0.39 W | 54–64 °C | 89–99 °C | 114–124 °C |
   | 1.5 A | 0.63 W | 73–88 °C | 108–123 °C | 133–**148** °C |
   | 2.0 A | 0.92 W | 94–117 °C | 129–**152** °C | 154–**177** °C |

   Range is RθJA 75–100 °C/W; this is **inference, not measured** — Vishay's 55 °C/W figure assumes
   14 × 14 mm pads and the SMC package, and this board gives D10 ~14 mm of 1 mm trace plus a 230 mm²
   inner-layer island through two 0.3 mm vias. Comfortable to ~1.5 A; marginal above that in a warm
   cabin. Confirm the device's actual draw.
4. **DG419 switching, on the bench.** Power the board, drive `SBU 1` from the comma device, and confirm
   both switches actually toggle. Two things to watch: the VL = 12 V threshold above, and the fact that
   R2+R3 put a **240 Ω pulldown** on `SBU 1` (≈ 14 mA at 3.3 V), which is a heavy load for a GPIO. Both
   are inherited from the working design, so this is confirmation rather than suspicion.
5. **J5/J6 orientation.** Electrically symmetric — all 12 nets are identical between them, so nothing in
   the netlist distinguishes harness side from ECU side. The J3+J5 / J4+J6 pairing comes from placement
   (shared x on each board edge). Confirm it matches how the two jumper harnesses are dressed; swapping
   them has zero electrical consequence.
6. **Enclosure fit.** J1 overhangs the board edge by 2.99 mm, J3/J5 by 1.47 mm, J4/J6 by 1.14 mm
   (`PM-002`). Expected for sealed edge-mount housings, but confirm against the enclosure cutout.
7. **Ground architecture change.** The reference kept a dedicated `Harness_GND` pass-through isolated
   from board GND. This board ties Fisker 14A (VBAT−) straight to board GND at J3.14/J4.14, so ECU
   return current and the comma device's ground reference share copper. Electrically this is a large
   improvement (2 mΩ vs 190 mΩ), and Fisker's own note says the primary ECU ground is through the
   housing to chassis so little current flows here — but it is a deliberate departure worth signing off.

---

## Design feedback (no rerouting expected)

Ordered by value. None of these block this build.

- **In2.Cu is a 7,600 mm² plane dedicated to `VIN`**, a net that carries 12.5 mA, plus a 230 mm²
  `12V_PROT` island. B.Cu signals therefore reference a power plane rather than ground. The reference
  board leaves In2 bare with GND on F/In1/B and scores slightly *worse* on EMC, so this is not a
  defect — but reallocating In2.Cu to GND is the single highest-value change for a future spin.
  (`GP-001` ×26, `SU-001`, `PS-002`.)
- **No decoupling within 10 mm of U1/U2** (`DC-002`). C2 (0.1 µF) is 35 mm from U1 and 40 mm from U2, so
  both DG419 V+/VL pins are effectively undecoupled. **The reference has the identical finding**, so it
  is inherited, not a regression. A 100 nF X7R at each part would be cheap next spin.
- **ESD diodes sit far from their connectors** — D2 22 mm from J4, D3 32 mm from J3, D8 37 mm from J5,
  and neither D2 nor D3 has a ground via at its ground pad (`ES-001`, `ES-002`). This one *is* a mild
  regression: the reference scores no `ES-001` findings.
- **Only 8 GND stitching vias** on a 115 × 75 mm board; ~50 % of the board has no ground via
  (`VS-002`). 27 vias total.
- **CAN pairs are not defined or routed as differential pairs** — one net class ("Default", 0.2 mm /
  0.2 mm), no diff-pair definitions. Worst intra-pair skew is `CMRR_RR` at 30.5 mm (36 %). At CAN FD
  rates the timing impact is negligible; the cost is EMC, since skew converts differential energy to
  common mode. For calibration, **the reference has a 27.2 mm / 48 % pair and works in a car.**
- **Two SMAJ16A in parallel** on `12V_PROT`. Harmless, but parallel TVS do not share surge current
  well — one larger device is usually the better call.
- **No ESD or filtering on the 18 pass-through nets** (four corner-radar CANFD pairs, DMS LED drive,
  six USS lines). Same as the reference, so consistent with prior practice, but worth a deliberate
  decision on an automotive interposer.
- **0 test points across 68 nets** (`TE-001`). Fine for a prototype; `12V_PROT`, `VIN`, `SBU 1` and the
  ADAS CAN pair would be the ones to add if this ever goes to ICT.
- **41 silkscreen DRC warnings** — `silk_over_copper` 17, `silk_edge_clearance` 12, `silk_overlap` 11.
  Cosmetic.
- **`lib_footprint_issues` ×17** — the `My_Components` library is not in the local library table. An
  environment issue, not a design defect, but it means library-level fixes (blocker 3, and the J1 peg-hole
  defect the prior review describes) cannot be made from this checkout.

---

## False positives / reviewer overrides

Considered and dismissed:

- **`connectivity_graph` island splits on `/12V_PROT`, `VIN` and D11.** The analyzer reports R5 isolated
  on both ends and D11 on its own island. Both are artifacts: the graph was built from the stale zone
  fill, and the analyzer matches endpoints only, so a track *crossing* a same-net pad (which is how D11
  connects) reads as a gap. KiCad DRC with `--refill-zones` reports 0 unconnected items.
- **`PM-002` connector edge overhangs** — intended for sealed edge-mount housings. Kept as a
  mechanical check, not an electrical finding.
- **`GP-001` / `SU-001` reference-plane findings** — heuristic (EMC trust level low, 0 % datasheet
  provenance). Retained as feedback, not blockers, because the proven board scores worse on the same
  rules.
- **Schematic-parity "Extra footprint H1 / H2"** — mounting holes with no schematic symbol, by design.
- **Prior review's "DRC 0 errors, 0 unconnected"** — true only after a zone refill, which is exactly
  blocker 1.

---

## Not performed / review limits

- **SPICE simulation** — no simulator installed (`ngspice`/`ltspice`/`xyce` all absent). No filter,
  divider or gain stage here would materially benefit.
- **Thermal analyzer** — ran, 0 findings, score `SKIPPED`: with no MPNs there is no θJA data, so it
  produced no usable result. D10 was hand-computed instead and is flagged as inference.
- **Lifecycle / obsolescence audit** — not run, no MPNs to query.
- **Gerber-level DFM** — no fabrication outputs exist in the repository.
- **Datasheet coverage (`DS-001`)** — no `datasheets/` directory and no MPNs. I obtained and read only
  the **DG419** (Vishay 61565) and **SS34** (Vishay 88751, SMC variant) datasheets. **PESD1CAN,
  SMAJ16A, the 1N4148W, the passives and the Molex/JAE connectors were not datasheet-verified** —
  findings involving them are internal-consistency or geometry checks.
- **Omron G5V-2-H1 pinout** was not re-fetched this session. The relay wiring is instead confirmed by
  exact pin-for-pin agreement with the reference design, which is field-proven with the same part
  family and the same footprint.
- **Molex 34691 customer drawing** could not be retrieved; connector pin numbering and keying remain
  unverified (see "Confirm before installing", item 1).
- Resistance, coil-voltage and junction-temperature figures are calculated from geometry and datasheet
  values, with assumptions stated inline — they are not measured.
