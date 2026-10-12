# Design Review — Ocean Harness

**Date:** 2026-10-12 | **Run:** `analysis/2026-10-12_1741-2/` | **KiCad:** 10.0 (schematic v20260306)
**Board:** 115.75 × 75.25 mm, 4-layer (F.Cu / In1.Cu=GND / In2.Cu / B.Cu), 22 components across 24 footprints, 69 nets, single sheet.

> **Changes applied during this review (2026-10-12).** The board was edited in-tree as the
> review progressed. In order: **U3 (L78L12) removed and replaced with R5**, a series dropper
> in the same footprint position; the **redundant J1 Edge.Cuts cutout deleted**; **two M3
> mounting holes added**; **3D models added** to J3/J4/J5/J6; **K1 changed to the
> high-sensitivity Omron G5V-2-H1 DC12**, with R5 rescaled 47 Ω → 160 Ω to suit the 960 Ω
> coil; and the **VBAT pass-through widened**, 61.4 mΩ → 24.6 mΩ. After every change KiCad
> DRC and ERC were re-run: **both report 0 errors**. The open blockers below are what remains.

## What this board is

An ADAS harness interposer for the Fisker Ocean. It breaks into the vehicle's main ADAS ECU connector (CON1, a 20-circuit section A plus a 16-circuit section B) and reproduces all 36 used pins: the vehicle harness lands on **J3 + J5**, and **J4 + J6** carry on to the ECU. Harness VBAT on pin 1A is reverse-protected by an SS34 (D10) into a `12V_PROT` rail, TVS-clamped by two SMAJ16A (D9/D11), and fed to a comma device over USB-C VBUS (J1). Of the 36 pins, only the vehicle CAN pair (HSCAN1, 19A/20A) is actually intercepted: a DPDT relay (Omron G5V-2-H1 DC12) is wired so the **normally-closed contacts connect harness↔ECU when unpowered** (fail-safe pass-through), and energising it hands the harness side to comma port A while comma port B stays wired to the ECU. Two DG419 SPDT analog switches (U1/U2) then select the final routing under an `SBU 1` logic input, with R4 switching a 120 Ω termination across the ECU-side pair. The mid-range radar CAN (1B/9B) is passed straight through with a listen-only tap to the comma device. The four corner-radar CANFD pairs, the DMS LED drive, and all six ultrasonic sensor lines are pure pass-throughs. PESD1CAN diodes (D1/D2/D3/D8) protect the intercepted and tapped CAN lines. The relay coil runs off `12V_PROT` through R5 (160 Ω), which holds it at its 12 V rating across the DC-DC output range.

## Verification basis

- **No BOM part carries an MPN property** (`SS-001`, `high`). Per this skill's contract, findings below are **consistency checks only** unless explicitly marked datasheet-verified.
- To close the gap on the parts where a wrong pin assumption would be board-killing, the manufacturer datasheets were pulled and verified pin-by-pin:

| Part | Ref | Library assumption | Datasheet (source) | Result |
|---|---|---|---|---|
| DG419LEDY-T1-GE4 (Vishay, SOIC-8 SPDT switch) | U1, U2 | 1=COM,2=NC,3=GND,4=V+,5=VL,6=IN,7=V-,8=NO | [Vishay Doc 61565 Rev B](https://www.vishay.com/docs/61565/dg417.pdf), p.1 pin diagram | **Match** — datasheet names pins 1/2/8 "D/S1/S2"; COM/NC/NO is a naming choice for the same pole/throw terminals. Pins 3–7 match exactly |
| G5V-2-H1 DC12 (Omron, DPDT signal relay) | K1 | Pins 1 & 16 = coil; 4/13 = COM | [Omron G5V-2 datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5v_2.pdf), "Terminal Arrangement/Internal Connections (Bottom View)" | **Match** — pins 1/16 are the coil (**no coil polarity**); pole 1 is COM=4, NC=6, NO=8 and pole 2 is COM=13, NC=11, NO=9. Read off the bottom-view diagram directly |
| G5V-2-H1 vs G5V-2 package | K1 | Same footprint and 3D body as the standard variant | Same datasheet, single **Dimensions** drawing covering the whole family | **Match** — eight 1 mm terminals on the same 2.54 / 5.08 / 7.62 mm grid, so the existing footprint and STEP model carry over unchanged |
| L78L12 / MC78L12A (SOT-89 regulator) | U3 *(removed)* | 1=OUT, 2=GND, 3=IN | [onsemi MC78L00A](https://www.onsemi.com/download/data-sheet/pdf/mc78l00a-d.pdf) | **Match**, but the part was wrong for the application — see "Design behavior" below |

No datasheet was obtained for the passives, PESD1CAN, SS34, SMAJ16A, or the Molex/JAE connectors — those remain consistency-only.

- **Fisker pinout cross-check:** all 36 used CON1 pins were verified at the **PCB pad level** (`pad_nets`), not just the schematic, so library footprint pad numbering is inside the check. Every used pin maps correctly, H/L polarity is consistent end to end, and nothing is wired to a pin the Fisker table marks NOT USED.
- **SPICE**: no simulator (`ngspice`/`ltspice`/`xyce`) installed — skipped. No filter/divider/gain circuit here would materially benefit.
- **Thermal**: ran, 0 findings — no components with computable power dissipation (no MPN-backed θJA data); not a meaningful result, treat as "not assessed."
- **Lifecycle audit**: not run — no MPNs to query.
- **Gerbers**: the `production/` export predates the current board files — not checked.
- **Prior review**: none found in the project directory.

---

## Blockers before fab

| # | Finding | Severity | Detail |
|---|---|---|---|
| 1 | **VBAT pass-through resistance** | High (electrical) | `Harness_12v` (pin 1A, J3.1→J4.1) carries the ECU's entire supply *plus* the comma device's. It was 124 mm of 1.0 mm trace = 61.4 mΩ; every segment has now been widened to its clearance-limited maximum, giving **24.6 mΩ** and a 3.9 A rating at 10 °C rise (narrowest section 1.95 mm). Still roughly **25× the ~1 mΩ of the 1.5–2.5 mm² OEM wire it replaces.** The long run is limited to 1.95 mm by a `VIN` via at (126.07, 70.61). **Fix:** blocker 2 — give the net copper on In2.Cu, which takes it to ~3 mΩ. **Also needed:** the ECU's actual VBAT budget, or at minimum the Molex 0346910200 per-circuit rating, to confirm 3.9 A is adequate in the interim |
| 2 | **In2.Cu plane allocation** (`GP-001` ×5 error + 21 warning, `SU-001`) | High (EMC / electrical) | In2.Cu is a **7,632 mm² plane dedicated to `VIN`**, which carries 12.5 mA, plus a 217 mm² `12V_PROT` island. Meanwhile the nets that carry amps are traces. Two consequences: the net needing copper doesn't have it (blocker 1), and **every B.Cu signal references a split power plane rather than ground** — 138 track segments including all the USS lines. Only **8 GND stitching vias** on a 115 × 75 mm board. **Fix:** reallocate In2.Cu to `Harness_12v` as a single continuous plane. **Prerequisite:** `VIN` has only 16.5 mm of track and lives entirely on the plane — reassigning it fragments `VIN` into 4 islands with 5 dangling vias (verified: DRC reports 3 unconnected items). `VIN` must be re-routed as traces first. Zone priorities can't avoid this: `VIN` runs top-left→bottom while `Harness_12v` runs left→right, so the two paths must cross on a single layer |
| 3 | **SS-001** — 0/13 BOM lines have an MPN | High (sourcing) | Every part is a `My_Components`/custom entry with no MPN property, even though real part numbers sit in the `Value` field (e.g. "G5V-2-H1 DC12", "Molex 0346910200"). Nothing is orderable through the standard sourcing workflow as-is, and this also blocks the thermal and lifecycle checks above. **Fix:** copy the value-field part numbers into the MPN property, or run the `bom` skill, before ordering |
| 4 | **FD-001** — 0 fiducials on F.Cu, 17 SMD parts | High (assembly) | No fiducials for pick-and-place vision alignment; finest pad dimension is 0.30 mm. Add ≥3 non-symmetric fiducials on F.Cu |
| 5 | **DC-002** — U1 and U2 have no decoupling capacitor within 10 mm | High (EMC/decoupling) | C2 (0.1 µF) sits at (127.8, 67.3); U1 is 35 mm away and U2 40 mm. Both DG419 V+/VL pins are effectively undecoupled. Add 100 nF X7R at each part's supply pins |
| 6 | **ES-002 / ES-001** — ESD diodes far from their connectors, no local ground via | High (ESD) | D2 is 22 mm from J4, D3 32 mm from J3, D8 37 mm from J5, and neither D2 nor D3 has a ground via at its ground pad. ESD energy crosses most of the board before being clamped. Move each PESD1CAN to within a few mm of its connector pads and put a ground via directly at the device's ground pin |

## High-value warnings (not blockers, worth fixing)

- **CAN pairs are not routed as differential pairs.** The project has **one net class** ("Default", 0.2 mm / 0.2 mm) and **no differential pair definitions at all**. Measured intra-pair length deltas: `CMRR_RR_CAN` 30.5 mm (36%), `CMRR_RL_CAN` 22.1 mm (27%), `ADAS_CAN` 20.3 mm (38%), `ADAS_CAN_C` 14.4 mm (40%), `MRR_CAN` 11.5 mm (7%). At CAN FD rates the ~180 ps of skew is irrelevant for *timing* (0.1% of a bit) — the problem is EMC: skew converts differential energy to common mode, and 30 mm of mismatch means the two conductors wander apart and open up loop area on an unshielded automotive bus. Add a `CAN` net class with a defined diff-pair width/gap, route each pair coupled, match within ~5 mm.
- **`VS-002`** — via stitching sparse: ~50% of the board has no ground vias. Compounds blocker 2.
- **No ESD protection on the pass-through lines.** The four corner-radar CANFD pairs, the DMS LED drive, and the six ultrasonic lines (18 nets) cross the board with no TVS and no filtering. The same was true of the passthrough reference design, so this is consistent with prior practice rather than a regression — but it is worth a deliberate decision for an automotive harness interposer.
- **USS power/ground at 0.25 mm.** `USS1/2_PWR` and `USS1/2_PWR_N` are POWER_VCC / POWER_GND pass-throughs routed at the signal default (≈0.85 A, 163 mΩ over 83 mm). Probably fine for DSI3 sensor banks, but these were sized by default rather than by intent.
- **DFM-001 / DFM-002** — 0.1 mm via annular ring is below IPC-6012 Class 2 (0.125 mm) and lands in JLCPCB's advanced tier. A 0.3 mm drill / 0.6 mm pad fixes it at no cost.
- **TE-001** — 0% test-point coverage across 68 nets. Fine for a prototype; add points on `12V_PROT`, `VIN`, `SBU 1` and the ADAS CAN pair if this goes to ICT.
- **D9 ∥ D11** — two SMAJ16A in parallel on `12V_PROT`. Harmless, but parallel TVS don't share surge current well; one larger device is usually the better call.
- **41 silkscreen DRC warnings** — `silk_over_copper` (18), `silk_edge_clearance` (12), `silk_overlap` (11). Cosmetic.
- **`lib_footprint_issues` ×17** — the `My_Components` footprint library is not in the local KiCad library table. Environment configuration, not a design defect, but it means library-level fixes (see the J1 note below) can't be made from this checkout.

## Design behavior worth confirming with the designer (not a defect)

- **U3's replacement with R5.** The board was drawn with an **L78L12 (U3)** generating a 12 V rail for the relay coil and the DG419 supplies, fed from `12V_PROT`. That part can never regulate here: it needs ≥14.5 V in, and this vehicle's DC-DC puts out 13.8–14.4 V, which after the SS34 drop gives 13.4–14.1 V at U3's input. It sat permanently in dropout, throwing away 1.7 V and pushing the guaranteed relay pull-in point up to a ~10.7 V rail. **U3 was removed and replaced with R5, a series dropper in the same footprint position.** A plain link was rejected: with the standard G5V-2's 120% (14.4 V) coil maximum, a direct connection would have sat the coil at or above its limit continuously. The value was set by the coil — 47 Ω for the original 288 Ω coil, rescaled to **160 Ω** when K1 became the 960 Ω H1, which reproduces the same operating curve within 0.04 V at every point.
- **The 12 V rail is a DC-DC, not an alternator.** This is an EV: there is no cranking event and no ISO 7637-2 pulse 5 load dump (a field-collapse phenomenon). The rail is held at 13.8–14.4 V by the HV-pack DC-DC when the vehicle is awake, and sits at the aux battery's resting voltage when asleep. The low-voltage case is a *degraded aux battery* — a slow, sustained condition — not a transient dip. This cuts both ways: it removes the brownout worry, but it also means any over-voltage on the relay coil would be **sustained** rather than occasional, which is what justifies R5.
- **K1 coil rating.** The coil is hard-tied across the rail through R5, so it is energised continuously the whole time the box is powered. The **standard G5V-2 DC12 is rated 120% max coil voltage = 14.4 V**; the **G5V-2-H1 DC12 is rated 180% = 21.6 V**, with the coil going from 288 Ω / 41.7 mA / ~500 mW to 960 Ω / 12.5 mA / ~150 mW. That removes the over-voltage margin problem, cuts ~29 mA of permanent quiescent draw, and reduces the coil self-heating that Omron's "Long-term Continuously ON Contacts" precaution warns about — which applies squarely to this circuit. Pick-up (75% max = 9.0 V) and drop-out (5% min = 0.6 V) are unchanged, so the fail-safe thresholds are the same. **Trade-off accepted:** max switching current 2 A → 1 A, far inside spec for CAN signalling at milliamps.
- **Relay topology.** Traced against the current netlist and the Omron bottom-view internal-connections diagram, each pole's common is the *harness* side and both throws are wired:

  | Pole | COM (pin) | NC (pin) | NO (pin) |
  |---|---|---|---|
  | 1 | `/ADAS_CAN_L` (4) → J3.19 | `/ADAS_CAN_L_MOD` (6) → J4.19 + J1.B3 | `/ADAS_CAN_L_C` (8) → J1.A3 |
  | 2 | `/ADAS_CAN_H` (13) → J3.20 | `/ADAS_CAN_H_MOD` (11) → J4.20 + J1.B2 | `/ADAS_CAN_H_C` (9) → J1.A2 |

  De-energised gives the fail-safe straight-through harness↔ECU path. Energising K1 does **not** open-circuit the harness pair — it hands each line to comma port A, while port B stays wired to the ECU, and the DG419s then select the final route under `SBU 1`. The relay and the analog switches are one two-stage path, not two independent ones.
- **J5/J6 orientation is an inference, not a derivation.** J3 vs J4 is *proven* by the relay commons sitting on J3's nets. J5 and J6, by contrast, are a completely symmetric pass-through — `CMRR_FR_CAN_H` = J5.2 ↔ J6.2 and so on for all 12 nets, with nothing in the netlist distinguishing them. The pairing J3+J5 (harness) / J4+J6 (ECU) comes from placement: J3/J5 share x=166.05 on the right edge, J4/J6 share x=114.53 on the left, so each side forms one cable bundle. **Confirm this against how the two jumper harnesses are actually dressed** — swapping J5/J6 has zero electrical consequence.
- **Ignition sense was dropped.** The passthrough reference drove the comma device's **SBU2** low through a MOSFET when `IGN` was active. V2 drops that circuit entirely and **J1.B8 (SBU2) is now floating**. Fisker CON1 has no ignition pin, so there was nothing to drive it from — this looks deliberate. The consequence depends on one unresolved fact: **is pin 1A switched or constant-battery?** If switched, VBUS presence is itself the ignition signal and this is fine. If constant, the comma device has no ignition input and no reason to sleep. **This matters more on an EV** — nothing tops the aux battery up during short trips, the DC-DC is off when the vehicle sleeps, and a flat aux battery on an EV can leave the car unable to close its HV contactors.
- **Ground architecture changed from the reference design.** The passthrough kept a dedicated harness-ground pass-through net separate from board GND, taking its reference from an external power connector. This board ties Fisker 14A (VBAT−) directly to board GND at J3.14 and J4.14, so the **ECU's full return current now flows through the board's ground plane**. With 13,833 mm² of GND on F+In1 that is electrically fine, but it means ECU return current and the comma device's ground reference share copper. Worth a conscious sign-off, especially given the Fisker note that the primary ECU ground is through the housing to chassis for EMC conformance.
- **J1 Edge.Cuts cutout — fixed here, still broken in the library.** The `My_Components:JAE DX07S024XJ1R1100` footprint drew the right-hand peg hole **twice**: a 0.775 mm round NPTH pad at (145.456, 106.394) *and* a 1.000 × 0.775 mm obround on Edge.Cuts at the same centre, 0.225 mm wider. The Edge.Cuts copy caused 3 `copper_edge_clearance` errors against J1's own GND pads; the NPTH hole underneath violated nothing, and the left peg never had a cutout at all. The 6 Edge.Cuts items were deleted from the board instance and DRC is clean, but **the library footprint still has the defect** and will reproduce it in the next project.
- **PM-002 edge overhangs (J1: 2.99 mm, J3/J5: 1.47 mm, J4/J6: 1.14 mm)** — all are at board edges consistent with their footprint orientation; these are sealed edge-mount harness connectors whose housings are meant to sit past the PCB edge. Very likely intentional, but confirm they clear the enclosure cutout.

## Cross-domain / connectivity

- Component count: schematic 22 vs PCB 24 footprints — **matches** (the two extra are the H1/H2 mounting holes, which have no schematic symbol by design).
- All 69 nets are present and routed; `routing_complete: true`, 0 unrouted nets, 0 unconnected items.
- Union-find connectivity analysis shows **every net as a single copper island** — no plane splits or orphaned copper.
- PCB pad-to-net mapping matches the schematic for all four harness connectors, checked pad by pad.
- Cross-analysis found only `VS-002` (sparse ground stitching); no ESD-gap (`EG-001`), decoupling-adequacy (`DA-001`), or schematic/PCB sync (`XV-00x`) findings — i.e. no swapped-pin or un-synced-net issues between schematic and layout.
- **KiCad DRC: 0 errors**, 58 warnings (silkscreen + the unresolved `My_Components` library). **KiCad ERC: 0 errors**, 76 warnings (mostly `pin_to_pin` type cosmetics from connector symbols using Unspecified pin types).

## What was not performed / limits

- **Full MPN-backed verification** of the passives, PESD1CAN, SS34, SMAJ16A, and the Molex/JAE connector pinouts — no datasheet obtained; findings involving them are internal-consistency checks only.
- **The ECU's VBAT current budget is unknown.** Blocker 1 cannot be closed without it. The Molex 0346910200 per-circuit rating was also not obtainable from public sources during this review.
- **SPICE simulation** — no simulator installed in this environment.
- **Thermal** — ran but produced no usable result (no MPNs → no θJA data). The D10 and R5 dissipation figures quoted elsewhere are hand-calculated, not tool-verified.
- **Lifecycle/obsolescence audit** — skipped, no MPNs to query.
- **Gerber-level DFM check** — the `production/` export predates the current board files and was not re-generated.
- **The layout findings predate the final edits in sequence.** GP-001, SU-001, DFM-00x and the placement findings were measured before the VBAT widening and the mounting holes were added. They should survive those changes — no zone boundary or component moved into their path — but they were not individually re-measured afterwards. DRC and ERC *were* re-run after every change.
- Trust rollup for this run: findings are a mix of deterministic topology checks and heuristic EMC rules (EMC trust level: **low**, 0% datasheet-backed provenance). Treat magnitude estimates (GP-001 coverage %, ES-001 overshoot) as heuristic engineering estimates, not measured values. The resistance, current-capacity and coil-voltage figures in this document are calculated from IPC-2221 and the component datasheets, and are stated with their assumptions.
