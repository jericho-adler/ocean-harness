# Ocean Harness — design review, 8 Nov 2026

Reviewed: `Ocean Harness.kicad_sch` / `.kicad_pcb` / `.kicad_pro` **as they sit in the working tree**, which for the
schematic is *not* what is committed. KiCad was not open (no lock files), so this covers everything on disk.

**Verdict: one blocker left — J1's annular ring. Everything else is clear.**

The reverse-polarity rework in the schematic is correct and datasheet-verified, and it fixes the one real
electrical problem the 2 Nov review raised. When this review was first written the board file had not been
updated to match it; **that rework has since been carried out on the PCB** and is described under
"Rework applied" below. Schematic and board now agree.

The 44 `hole_clearance` errors from the last review are gone. DRC is clean: 0 errors, 0 unconnected items.

---

## Rework applied, 8 Nov 2026

D10 was removed and the P-FET group placed and routed. What changed on the board:

| | |
|---|---|
| Removed | D10 (MBRA340T3G, SMA) and its two trace stubs |
| Added | **Q1** `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` at (153.0, 70.81) rot 180 — drain pads 5–8 on `VBAT_FUSED`, source pads 1–3 on `12V_PROT`, gate pad 4 on the new `Q1_GATE` net |
| Added | **D15** `Footprints:SOD123_DIO` at (157.9, 70.3) rot 90 — cathode on `12V_PROT`, anode on `Q1_GATE` |
| Added | **R7** `Footprints:Rohm ESR03EZPJ104` at (160.5, 69.5) rot −90 — `Q1_GATE` to GND, with a stitching via to the In1.Cu plane |
| Moved | FID2 (160.5, 72.5) kept; F1's reference text off Q1 pad 8; "CAR HARNESS-->" relocated and resized |

**Where it went, and why not in D10's slot.** D10 sat between J1 and J3 in a pocket 4.50 mm wide
(J1's pads reach x=132.28, J3's courtyard starts at 137.03). A SOIC-8 needs 7.4 × 5.4 mm and does not fit there
in either orientation, and neither does it fit after relocating D11 — the widest clear channel in that whole
cluster is 5.06 mm against U1. The group went instead into the gap between J5 and J3, immediately after F1,
which is the only free area on the board large enough and is electrically the better place for it.

**Consequences of that choice:**

- `VBAT_FUSED` — the unprotected rail — drops from **47.1 mm to 6.2 mm**. Almost nothing on the board now sits
  upstream of the reverse-polarity FET. This is a real improvement over the old arrangement.
- `12V_PROT` takes over the long right-edge run, **20.3 mm → 85.1 mm**, reusing the exact copper `VBAT_FUSED`
  used to occupy (re-netted, 1.2 mm) plus a new 1.2 mm link up through D10's old slot to D11/D9/C1/R5.
  At 2 A that is about a 5 °C rise by IPC-2221, and much of it is backed by the In2.Cu island.
- D9/D11 now sit roughly 45 mm downstream of Q1 rather than beside it. This is the one thing the move costs,
  and it is worth being explicit about: during a fast transient the trace inductance between Q1 and the clamps
  means Q1 briefly sees more than the clamped rail. It is not a problem for V<sub>DS</sub> — Q1 is in
  conduction, so drain and source rise together and V<sub>DS</sub> stays near zero, against a −40 V rating.
  V<sub>GS</sub> is the parameter that matters, and **D15 is 2.4 mm from Q1's gate pad**, so it clamps locally
  regardless of what the far end of the rail is doing. If you want belt-and-braces on a later revision, moving
  one SMAJ16A next to Q1 would close this out.
- Under reversed polarity nothing conducts: Q1's channel is off, its body diode is reverse-biased, and
  `12V_PROT` never rises, so D9/D11 stay off and **F1 survives**. The fuse is not sacrificial here.

**Verification after the rework** — `kicad-cli pcb drc --schematic-parity --refill-zones`:

| | Before rework | After rework |
|---|---|---|
| DRC errors | 0 | **0** |
| Unconnected items | 0 | **0** |
| Schematic-parity issues | 13 (3 missing footprints, D10 orphaned) | **9 — identical to the committed board** |
| DRC warnings | 42 | 43 |
| Cross-domain findings | 3 | **0** |
| Footprints | 33 | 35 |

The 9 parity items are the five expected mechanical `extra_footprint` entries (H1, H2, FID1–3) and four
pre-existing `Description`/`Spec` field-text drifts on C3, D12, D13 and R6 that were there before this work.
Q1, D15 and R7 contribute none — their fields were aligned to the schematic. The single extra DRC warning is
`lib_footprint_issues`, from the two library names the new footprints reference that are not registered on this
machine (finding 4); it is the same class as the 20 already present.

Silkscreen in that gap was congested, so three deliberate trade-offs were made: the reference text for Q1, D15
and R7 is on **F.Fab rather than F.SilkS**, D15's cathode bar is on F.Fab too (on silk it landed on Q1 pad 2),
and "CAR HARNESS-->" moved to the central channel below the Fisker logo at size 1.2 (at 1.5 it is ~22 mm and
does not fit the 20.2 mm strip). Net effect: `silk_over_copper` went **down**, from 3 to 2, and every remaining
silk warning is pre-existing. If you want designators on silk for those three parts, they will need hand-placing
in KiCad.

---

## Critical findings

| # | Severity | Finding | Basis |
|---|---|---|---|
| 1 | ~~Blocker~~ **Resolved** | Schematic and PCB described different circuits — the board still had D10 and none of Q1/R7/D15. Reworked on 8 Nov; see "Rework applied" above | DRC schematic-parity, raw-file verified |
| 2 | **Blocker** | J1's row-B through-hole pads are 0.65 mm copper on a 0.45 mm drill → **0.10 mm annular ring**, on pads carrying the ECU-side CAN pair and half the 12 V feed. Unfixed from the 2 Nov review | Raw-file verified |
| 3 | Medium | Q1, R7 and D15 have no LCSC/JLCPCB part number; R7 and D15 have no MPN at all. R6's JLCPCB field is still empty | Raw-file verified |
| 4 | Medium | The custom symbol and footprint libraries are not registered — there is no `fp-lib-table` or `sym-lib-table` in the project or in `~/.config/kicad/10.0/` | Verified on this machine |
| 5 | Medium | Bottom-layer signals reference a **split power plane** (In2.Cu carries VIN and a 12V_PROT island), not ground. 158 of 357 segments are on B.Cu | Analyzer-derived |
| 6 | Medium | The corner-radar CANFD pairs and the DMS LED pair still have **no ESD protection** despite landing on vehicle-harness connectors | Raw-file verified |
| 7 | Low | R4 termination lands at 131–138 Ω, outside CAN's 108–132 Ω window at the hot end | Datasheet-verified |

### 1 — Schematic and PCB were out of sync *(resolved 8 Nov — see "Rework applied")*

The schematic work replaced the series Schottky reverse-polarity diode with a P-channel MOSFET
ideal-diode pass element. As originally found, the board had not followed:

| Ref | Part | Status in schematic | Status on board |
|---|---|---|---|
| D10 | MBRA340T3G, SMA | **removed** | still placed and routed at (134.78, 105.60) |
| Q1 | DMP4015SSSQ-13, SO-8 | added | **missing** |
| R7 | 100 K, 0603 | added | **missing** |
| D15 | BZT52C16, SOD-123 | added | **missing** |

`kicad-cli pcb drc --schematic-parity` reports 13 parity issues against the working-tree schematic: three
`missing_footprint` (Q1, R7, D15), six `extra_footprint` (H1, H2, FID1–3 as expected, **plus D10**), and four
cosmetic field-text mismatches.

Run against the committed schematic, the same board gives 9 parity issues — the five expected mechanical
`extra_footprint` entries and four field mismatches, with no missing footprints. So `HEAD` is self-consistent and
the working tree is not. The desync is entirely the new rework.

**This is not a drop-in swap.** D10's SMA courtyard is 3.5 × 7.0 mm and sits 0.35 mm from the bottom board edge,
5.2 mm from J3, with D11 0.95 mm clear above it. Q1's SOIC-8 courtyard is about 5.4 × 6.0 mm — roughly 1.9 mm
wider in the axis that is currently pinned by the board edge — and R7 and D15 need to go somewhere in the same
pocket. Expect to move D11/C1, re-route the local `VBAT_FUSED` and `12V_PROT` copper, and refill.

Pick one before you order:

- **Finish the rework**: place Q1/R7/D15, remove D10, re-route that corner, refill, re-run DRC to zero errors and
  zero parity issues. This is the right answer — see "The reverse-polarity rework" below for why.
- **Fabricate `HEAD` instead**: `git stash` the schematic, build the committed design, and accept D10's thermal
  headroom problem (finding 3 of the 2 Nov review, still unresolved in that version).

Do not fabricate the working tree as it stands. The Gerbers would come from the board file, so you would get the
D10 circuit while your BOM, schematic and documentation describe the Q1 circuit.

### 2 — J1 annular ring

J1 (JAE DX07S024XJ1R1100) is a hybrid USB-C: row A is SMD (0.3 × 1.1 mm pads), row B is through-hole.

| Pad group | Count | Pad | Drill | Annular ring |
|---|---|---|---|---|
| J1 row B (B1–B12) | 12 | 0.65 mm | 0.45 mm | **0.100 mm** |
| J1 shell legs (S1) | 4 | 1.15 × 2.3 mm oval | 0.65 mm | 0.250 mm |
| J3/J4/J5/J6 signal pins | 72 | 1.778 mm | 1.27 mm | 0.254 mm |
| K1 | 8 | 1.5 mm | 1.0 mm | 0.250 mm |
| Vias | 54 | 0.5 mm | 0.3 mm | 0.100 mm |
| Vias | 10 | 0.6 / 0.8 mm | 0.3 / 0.4 mm | 0.150 / 0.200 mm |

Row B is not decorative. It carries `ADAS_CAN_H_MOD` / `ADAS_CAN_L_MOD` on B2/B3 — the ECU-side half of the
intercepted bus — plus VBUS on B4/B9 and GND on B1/B12. A registration breakout on one of those is an
intermittent on a safety-relevant CAN pair inside a vehicle.

0.10 mm is below the 0.125 mm figure the DFM analyzer cites for IPC-6012 Class 2, and below the standard-process
minimum at most prototype fabs (JLCPCB and PCBWay both want ≥0.13–0.15 mm on PTH component pads). The 0.5/0.3 mm
vias are also at 0.10 mm, but that is a stock via size that fabs do accept — the component pads are the exposure.

Enlarging J1's row-B pads to 0.75–0.80 mm gets you to 0.15–0.175 mm and inside Class 2. Note that this is what
caused the 44 `hole_clearance` errors in the 2 Nov review: the zone pours reach into J1, and at a larger pad you
will need a local clearance rule or a small keepout around J1 as well. Refill and re-run DRC after.

The alternative is to confirm with your fab in writing that they will run 0.10 mm rings on 0.45 mm holes.

---

## The reverse-polarity rework — verified correct

This is the substantive change since the last review, and it is well done. Verified against the Diodes
Incorporated **DMP4015SSSQ** datasheet (document DS36682 Rev. 7-2, December 2023), fetched and read directly.

### Topology

```
F1 (3 A) ── VBAT_FUSED ──┬── Q1 drain (pads 5-8)
                         │
                   Q1 ───┴── Q1 source (pads 1-3) ── 12V_PROT
                         │
                   Q1 gate (pad 4) ──┬── R7 100 K ── GND
                                     └── D15 BZT52C16 (anode) ─ cathode ─ 12V_PROT
```

**Orientation is right.** Drain on the input, source on the output. For a P-channel device the body diode runs
drain→source, so it conducts battery-to-load and blocks load-to-battery — which is what makes the reverse case
safe. Gate pulled to GND through R7 gives V_GS = −V(12V_PROT), turning the FET hard on in normal operation. Under
reverse polarity the source sits near 0 V with the input negative, V_GS collapses to ~0, the FET is off, and the
body diode is reverse-biased. Correct in both states.

### Datasheet verification

| Spec | Datasheet (page) | This design | Verdict |
|---|---|---|---|
| Package | SO-8 (p.1, Mechanical Data) | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | Correct land pattern |
| Pin configuration | pins 1–3 S, 4 G, 5–8 D (p.1, Pin Configuration) | symbol maps 1–3 S, 4 G, 5–8 D | **Exact match** |
| V_DSS | −40 V (p.2) | ~14 V reverse worst case | Large margin |
| V_GSS | **±25 V** (p.2) | clamped to ~16 V by D15 | Correct, and D15 is required |
| R_DS(on) | 11 mΩ max @ V_GS = −10 V (p.2) | V_GS ≈ −14 V running | 11 mΩ applies |
| I_D | −10.1 A @ 25 °C, −8 A @ 70 °C (p.2) | 3 A fuse limit | Large margin |
| V_GS(th) | −1.5 / −2 / −2.5 V (p.2) | — | Fully on well below normal rail |
| C_iss | 4,234 pF typ (p.2) | with R7 = 100 K → τ ≈ 423 µs | Soft start, see below |
| RθJA | 88 °C/W min pad, 70 °C/W with 1 in² (p.2) | see thermal | Fine |
| T_J | −55 to +150 °C (p.2) | automotive ambient | Fine |
| Qualification | AEC-Q101, PPAP capable, IATF 16949 (p.1) | automotive application | Right part for the job |

**D15 is doing real work.** Without it, V_GS equals the full rail voltage. D9/D11 (SMAJ16A) clamp a transient at
around 26 V, which would put V_GS at −26 V against a ±25 V absolute maximum. The 16 V zener keeps it inside.
Orientation is correct: cathode on the source (12V_PROT), anode on the gate, so reverse breakdown clamps in the
direction the gate actually swings. At the ~100 µA that R7 passes during a clamp event the BZT52C16 will break
down somewhat below its 16 V nominal — that errs in the safe direction.

**R7 at 100 K is sound.** Gate leakage is 100 nA max (I_GSS, p.2), so the standing offset across R7 is 10 mV.
With C_iss at 4,234 pF the turn-on constant is ~423 µs, giving a 1–2 ms soft start that limits inrush into C1 and
the comma device. During that window current flows through the body diode (V_SD −0.7 V typ, −1 V max at 1 A),
which is a few millijoules — immaterial.

### The thermal problem is solved

| | D10 (MBRA340T3G, SMA) | Q1 (DMP4015SSSQ, SO-8) |
|---|---|---|
| Drop mechanism | ~0.45 V forward | 11 mΩ × I |
| At 2 A | **0.9 W** | **0.044 W** |
| At 3 A (fuse limit) | **1.5 W** | **0.099 W** |
| Rise at 3 A | ~112 °C (75 °C/W) | ~8.7 °C (88 °C/W) |

Finding 3 of the 2 Nov review — "inside a vehicle enclosure at 60–85 °C ambient, the 3 A case exceeds the 150 °C
junction limit" — is fully resolved. A twenty-fold reduction in dissipation.

### Side effect on the relay coil

Dropping the ~0.45 V Schottky drop raises `12V_PROT` by the same amount, and `VIN` with it through the
R5/coil divider (160 Ω against the 960 Ω coil, ratio 0.857):

| Rail | Old (D10) | New (Q1) | Coil rating |
|---|---|---|---|
| 14 V | VIN ≈ 11.6 V | VIN ≈ **11.97 V** | 12 V nominal |
| 16 V | VIN ≈ 13.3 V | VIN ≈ 13.7 V | 21.6 V max (`-H1`) |

This is an improvement — at a normal charging rail the coil now sits essentially exactly at its 12 V rating, and
the 16 V case still has good margin. Coil dissipation rises from 150 mW to ~195 mW at 16 V. No action needed.

One behavioural note: a MOSFET channel conducts both ways, so unlike the Schottky, Q1 does not block current from
`12V_PROT` back into the harness while it is on. Nothing on this board sources into `12V_PROT`, and the comma
device is a sink on VBUS, so this is a non-issue — but it is a real difference from the old circuit.

---

## What else is verified correct

### Connector passthrough — verified pin by pin

Every carried circuit lands on the same pin number on both sides, and the only pins that differ are exactly the
two the relay intercepts. This is the heart of the board and it checks out.

| | J3 → J4 (section A, 20-way) | J5 → J6 (section B, 16-way) |
|---|---|---|
| Identical both sides | 1, 6, 7, 14, 15, 16, 17, 18 | 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 15, 16 |
| Intentionally different | 19 (`ADAS_CAN_L` → `ADAS_CAN_L_MOD`), 20 (`ADAS_CAN_H` → `ADAS_CAN_H_MOD`) | none |
| Unconnected both sides | 2, 3, 4, 5, 8, 9, 10, 11, 12, 13 | 6, 7, 8, 14 |

### Relay contact assignment

Unchanged since the 2 Nov review, where it was verified against the G5V-2 datasheet terminal-arrangement diagram:
COM = 4/13 (vehicle), NC = 6/11 (ECU), NO = 8/9 (comma), coil on 1/16. De-energised gives a hard-wired
vehicle↔ECU passthrough. The fail-safe is wired the right way round.

### CR1 flyback polarity

Pad 1 (cathode) on `VIN`, pad 2 (anode) on GND, across the coil between K1.16 (`VIN`) and K1.1 (GND). Reverse
biased in normal operation, conducts on coil collapse. Correct.

Note: the analyzer reports CR1's pins twice because the `1N4148W-7-F` library symbol carries two De Morgan body
styles (`_1_1` and `_1_2`) with pins at different offsets. That is a symbol-library artifact, not a wiring fault —
only one body style is instantiated.

### U1 / U2 switch logic and R4

`SBU 1` low → NC on → `_C` bridged to `_MOD` on both lines, device listening. `SBU 1` high → NO on → U1 routes
`ADAS_CAN_H_MOD` through R4 to `ADAS_CAN_L_MOD`, terminating the isolated ECU segment. U2's NO pin is
intentionally unused; only one switch is needed to place R4 across the pair. R2+R3 give the 240 Ω pulldown that
makes "low" the power-on default. All correct.

### DRC

**0 errors, 0 unconnected items, routing complete.** The 44 `hole_clearance` errors from 2 Nov are gone —
commit `061bd22` refilled the zones and cleared them.

42 warnings remain, all cosmetic or library hygiene:

| Count | Type | Assessment |
|---|---|---|
| 20 | `lib_footprint_issues` | Library hygiene |
| 10 | `silk_edge_clearance` | Silk clipped at board edge |
| 6 | `silk_overlap` | Cosmetic |
| 3 | `silk_over_copper` | Cosmetic |
| 3 | `lib_footprint_mismatch` | Local footprint differs from library |

### ERC

107 warnings, 0 errors. None are wiring faults:

| Count | Type | Assessment |
|---|---|---|
| 38 | `pin_to_pin` | Unspecified pin types on connector and relay symbols |
| 25 | `endpoint_off_grid` | Cosmetic |
| 22 | `footprint_link_issues` | Library pathing |
| 19 | `lib_symbol_issues` | Libraries not registered — see finding 4 |
| 3 | `lib_symbol_mismatch` | Cached symbols differ from library |

The two `isolated_pin_label` findings from 2 Nov are resolved — the dead `COMMA_P`/`COMMA_N` labels were removed
in `7af170a`. J1 B10/B11 are now plain unconnected pins. The two `same_local_global_label` findings are also gone.

### SPICE

ngspice-42, 6 subcircuits, **6 pass / 0 warn / 0 fail / 0 skip**, 0.10 s. R2/R3 divider arithmetic exact;
`12V_PROT` PDN 509 mΩ at 1 MHz, `VIN` 1.62 Ω at 1 MHz. As last time, this board has very little analog content to
verify, and the protection "pass" results mean presence, not measured clamping behaviour.

### Power and current capacity

| Net | Min width | Length | Verdict |
|---|---|---|---|
| `Harness_12v` (ECU passthrough) | 2.4 mm trunk (B.Cu) | 97.4 mm | ~13 °C at 5 A. Fine |
| `VBAT_FUSED` | 1.2 mm | 47.1 mm | ~5 °C at 2 A, ~13 °C at 3 A. Fine |
| `12V_PROT` | 0.25 mm stubs, 1.0 mm trunk | 20.3 mm | Fine — see below |
| `VIN` | 0.5 mm | 15.6 mm | ~13 mA coil current. Fine |

The two 0.25 mm `12V_PROT` segments are 1.31 mm stubs feeding J1's A4/A9 **SMD** VBUS pads, each paralleled by a
0.5 mm B.Cu run. The bulk current reaches J1 through the In2.Cu 12V_PROT island and the B4/B9 through-holes. With
the load split four ways these stubs see ~0.5 A, a ~3 °C rise. Not a problem.

One genuinely narrow spot: a **0.6 mm, 1.6 mm-long** `Harness_12v` segment at (144.10, 71.95)→(144.10, 73.55)
feeding F1's input pad. At the 3 A fuse limit IPC-2221 gives ~39 °C for an infinitely long trace; over 1.6 mm with
heat spreading into the adjacent 1.2 mm and 2.4 mm copper the real figure is far lower. Worth widening to 1.2 mm
for consistency while you are in there, but not a blocker.

---

## Should fix before ordering

### 3 — BOM gaps

| Ref | Value | MPN | JLCPCB / LCSC |
|---|---|---|---|
| Q1 | DMP4015SSSQ-13 | present | **missing** |
| R7 | 100 K | **missing** | **missing** |
| D15 | BZT52C16 | **missing** | **missing** |
| R6 | 3.3 K | ESR03EZPJ332 | **empty field** |

The other 26 parts all carry both. R6's empty JLCPCB field has been outstanding since the October review.

### 4 — Libraries are not registered

There is no `fp-lib-table` or `sym-lib-table` in `PCB Files/`, and the global tables in `~/.config/kicad/10.0/`
contain only the stock `KiCad` entry. `My_Components`, `Footprints` and the two date-named libraries do not
resolve — which is what the 19 ERC `lib_symbol_issues` warnings are reporting.

Practical consequences: the README's "run Tools > Update Footprints from Library on F1 and D14" step cannot work,
and placing R7 and D15 needs `Footprints:Rohm ESR03EZPJ104` and `Footprints:SOD123_DIO`. (Q1's
`Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` is stock KiCad and will resolve.) `SOD123_DIO` is already embedded in the
board via CR1 and D13 so it can be copied, but registering the libraries properly is the clean fix.

Note that `.gitignore` deliberately excludes both tables as machine-specific, so this will not show up in a fresh
clone either.

### 5 — B.Cu signals over a split plane

Unchanged from 2 Nov. F.Cu signals sit 0.21 mm above a solid ground plane — excellent. B.Cu signals sit 0.21 mm
below In2.Cu, which is split between a `VIN` pour and a `12V_PROT` island, so their nearest reference is
discontinuous. The stackup declares In2.Cu as a *signal* layer, and EMC flags `SU-001` "adjacent signal layers:
In2.Cu, B.Cu" alongside 17 error-level and 11 warning-level `GP-001` reference-plane-gap findings and 19
`RP-001` missing-stitching-via findings. With 158 of 357 segments on B.Cu this is not a corner case.

At CAN and CAN FD rates this will not stop the board working. It is an emissions and susceptibility risk, which
matters more in a vehicle than on a bench. Cheap mitigations: add ground stitching vias along the B.Cu routes
(`VS-002` reports 50 % of the board lacks ground vias) and keep B.Cu runs over the GND pour rather than crossing
the VIN/12V_PROT split.

### 6 — ESD coverage gaps

Four PESD1CAN arrays cover the vehicle-side ADAS CAN (D3), the ECU-side pair (D2), the MRR tap (D8) and the
comma-side `_C` pair (D1), and D14 covers `SBU 1`. The four corner-radar CANFD pairs (CMRR FR/RR/FL/RL) and the
DMS LED pair have none, despite landing directly on vehicle-harness connectors. That is eight unprotected
harness-facing nets.

Also `ES-001`: D3 is far from J5, so its ESD return path is longer than it should be.

### 7 — R4 termination value

With `SBU 1` high, the ECU-segment termination is R4 in series with one DG419 R_DS(on): 11 Ω typical, 14 Ω max at
room, 18 Ω max over −40 to +85 °C. That puts the termination at **131–138 Ω** against CAN's 120 Ω ±10 %
(108–132 Ω) — marginally out at the hot end and worst when cold. A **100–110 Ω** R4 centres it.

### Series resistance in the default powered state

Worth re-stating from 2 Nov because it has not changed: with `SBU 1` low, the vehicle↔ECU CAN path runs through
**both** DG419s, picking up 22–36 Ω of differential loop resistance. Against a 60 Ω effective bus load that is a
real divider — a 2 V differential drive could arrive near 1.25 V against a ~0.9 V dominant threshold. It will
probably work, but the margin is thinner than it looks and it is worst when cold. Bench-test this mode at −40 °C
if you can. Full-intercept mode (`SBU 1` high) takes the switches out of the path and does not suffer this.

### Other layout items

- **PM-002 ×7** — D1 at 0.37 mm and D10 at 0.35 mm from the board edge (≥1.0 mm recommended); J1/J3/J4/J5/J6
  courtyards overhang the outline by 1.1–3.0 mm. The connector overhangs are intentional for edge-mounted
  housings. The diodes are worth nudging inward — and D10's position is about to be reworked anyway.
- **TE-001** — no test points on any of 71 nets. For a board that sits inline in a vehicle harness, pads on
  `12V_PROT`, `SW_VCC`, `SBU 1` and the ADAS CAN pairs would make bring-up much easier.
- **DC-001** — C2 moderately far from U2. **BE-001** — `SW_VCC` routed near the board edge.
- **IO-002 ×4** — J3–J6 have few or no ground pins. Dictated by the Fisker CON1 pinout, not a choice you can make.
- **DFM-001/002** — the board is on JLCPCB's *advanced* tier solely because of the 0.10 mm annular ring.
- **Relay continuously energised** — Omron's G5V-2 datasheet (p.4, "Long-term Continuously ON Contacts") warns
  that coil self-heating can film the contacts. The design is fail-safe (de-energised = stock passthrough), so the
  consequence is degraded intercept rather than a dead car, but exercising the relay periodically in firmware
  would help.

### Documentation drift

`README.md` and `OVERVIEW.md` both describe D10 as an **SS34**. The committed board has an **MBRA340T3G**
(swapped in `7af170a`), and the working-tree schematic has no D10 at all. `OVERVIEW.md` also states "there is no
MOSFET on this board", which the Q1 rework makes false, and still quotes the old 115.75 × 75.25 mm-era part count.
Both need a pass once the rework lands.

The README's "Before you build" list is also now stale: item 2 (R6 has no JLCPCB part number) is partly done — R6
has an MPN but still no LCSC code — and items 3 and 4 remain open.

---

## False positives / reviewer overrides

- **PP-001 ×2 (error) — "U1.4 / U2.4 V+ has no DC path to a power rail"** — dismissed, as in the 2 Nov review.
  The path is `12V_PROT` → R5 → `VIN` → D12 → `SW_IN` → R6 → `SW_VCC`. The analyzer's 2-hop BFS does not accept a
  series Schottky as a conducting edge.
- **RS-001 — "VBAT_FUSED has no declared source"** — PWR_FLAG hygiene, not a wiring fault. The rail is sourced
  from J3 pin 1 through F1; connector pins are passive so the analyzer sees no declared source.
- **CR1 pins reported twice** — De Morgan body-style artifact in the library symbol, described above.
- **PM-002 connector courtyard overhangs (J1, J3–J6)** — intentional for edge-mounted housings.
- **CP-002 ×4 — "no opposite-layer copper under H1/H2/FID"** — expected for mounting holes and fiducials.
- **DRC `silk_*` warnings (19)** and **ERC `pin_to_pin` ×38** — cosmetic / library metadata.

---

## Not performed / review limits

- **Gerber analysis not performed** — no fabrication outputs in the tree.
- **Lifecycle / obsolescence audit not performed** — no distributor API credentials in the environment
  (`DIGIKEY_CLIENT_ID`, `MOUSER_SEARCH_API_KEY`, `ELEMENT14_API_KEY` all unset). 28 of 30 parts have MPNs, so this
  would run if credentials were added.
- **Datasheet coverage is partial.** There is no `datasheets/` directory. For this review I fetched and read the
  **DMP4015SSSQ** datasheet directly (DS36682 Rev. 7-2) — every Q1 claim above is cited to it. The G5V-2, DG41xLE,
  PESD1CAN and JAE connector findings carry over from the 2 Nov review, where they were verified against PDFs
  extracted from the board file's `embedded_files` block. **SS34/MBRA340T3G, SMAJ16A, DSK14, BZT52C12, BZT52C16,
  1N4148W, the Molex connectors and F1 remain inference-only**, including the load-dump clamp numbers.
- **Thermal analyzer assessed 0 components** — it finds no quantifiable dissipation, which is correct for a board
  with no regulator. The thermal figures above are hand-computed from datasheet θJA.
- **Molex pin numbering and polarization against the real Fisker CON1 keying is still unverified**, and cannot be
  settled from the design files. Outstanding since October.

---

## Before fabricating

1. ~~Decide which circuit you are building~~ — **done.** The Q1/R7/D15 rework is on the board, D10 is gone, DRC
   is at zero errors and parity matches the committed baseline.
2. **Fix J1's annular ring** to 0.15 mm or better, or get written confirmation your fab will run 0.10 mm. Expect
   the J1 hole-clearance errors to return when you enlarge the pads — add a local clearance rule or keepout.
   *This is the one remaining blocker.*
3. Add MPNs and LCSC numbers for Q1, R7, D15; fill R6's JLCPCB field.
4. Register the custom symbol and footprint libraries, then run Tools > Update Footprints from Library on F1,
   D14, D15 and R7 and re-run DRC.
5. Open the board in KiCad once and eyeball the J5↔J3 gap — the rework was done outside the GUI, and DRC
   cannot tell you whether the result reads well to a human.
6. Add ground stitching along the B.Cu routes; keep B.Cu signals off the In2.Cu power split.
7. Consider: ESD arrays on the four CMRR pairs and the DMS LED pair, R4 at 100–110 Ω, a few test points,
   widening the 0.6 mm F1 feed, and moving one SMAJ16A next to Q1.
8. Still outstanding and not resolvable from the design files: **verify the Molex connector pin numbering and
   polarization against the real Fisker CON1 keying before installing in a vehicle.**

## Analyzers run

`analyze_schematic.py`, `analyze_pcb.py --full --proximity`, `cross_analysis.py`, `analyze_emc.py`,
`analyze_thermal.py`, `simulate_subcircuits.py` (ngspice-42), plus `kicad-cli pcb drc --schematic-parity`
(working tree *and* `HEAD`) and `kicad-cli sch erc`. Raw-file verification via `sexp_parser` for symbol
geometry, pad/via annular rings, net tracing and duplicate-reference checks. DMP4015SSSQ datasheet fetched and
read directly.
