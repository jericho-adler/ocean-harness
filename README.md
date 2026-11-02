# Ocean Harness

An automotive ADAS harness interposer designed in KiCad, built for the **Fisker Ocean**. It sits inline on the main ADAS ECU connector (CON1) and provides a fail-safe electrical bypass plus signal switching for a comma device, protected against automotive power-rail transients and ESD.

![Assembled board render, showing the harness-side and ECU-side connectors](3D%20models/Ocean%20Harness.png)

- **Board:** 89.0 × 72.2 mm, 4-layer (F.Cu / In1.Cu=GND / In2.Cu=power / B.Cu), 26 components across 31 footprints (the extra five are two M3 mounting holes and three fiducials, none of which have a schematic symbol), 71 nets
- **Harness interposition:** the vehicle harness lands on **J3 + J5**; **J4 + J6** carry on to the ADAS ECU. J3/J4 are 20-circuit (CON1 section A) and J5/J6 are 16-circuit (CON1 section B), so the board reproduces all 36 circuits of the Fisker pinout, of which 22 are populated
- **Power:** self-powered from harness VBAT (pin 1A) — no external supply needed. Reverse-protected by an SS34 Schottky into a `12V_PROT` rail, TVS-clamped by two SMAJ16A, and passed to the comma device over USB-C VBUS
- **Fail-safe passthrough:** a DPDT relay (Omron G5V-2-H1 DC12) wired so the normally-closed contacts connect the vehicle CAN (HSCAN1, pins 19A/20A) straight through to the ECU when the box is unpowered, and hand it to the comma device when energised. The coil runs off `12V_PROT` through a 160 Ω dropper (R5) that holds it near its 12 V rating at a normal ~14 V charging-system rail; the high-sensitivity `-H1` variant is used for its 150 mW coil (vs 500 mW) and 180% max coil voltage (21.6 V), which matters because the coil is energised continuously whenever the box is powered
- **Switch supply:** the analog switches run from their own `SW_VCC` rail rather than off the coil supply — a DSK14 Schottky (D12) blocks the dip when the relay coil pulls in, C3 holds the rail up across it, and R6 + a BZT52C12 Zener (D13) clamp it to 12 V so the switches never see the full VBAT range
- **Signal switching:** two DG419 SPDT analog switches route the CAN pairs under control of an `SBU 1` logic input from the comma device, with a switched 120 Ω bus termination (R4). R2 + R3 pull `SBU 1` low so the default is the transparent, bridged state
- **Protection:** PESD1CAN ESD diodes on the intercepted and tapped CAN lines
- **Pass-through only:** the four corner-radar CANFD pairs, the DMS LED drive, and all six ultrasonic sensor lines run straight across the board untouched; the mid-range radar CAN is passed through with a tap to the comma device

## Documentation

[`OVERVIEW.md`](OVERVIEW.md) — what the board does, connector by connector and rail by rail, including the relay/analog-switch truth table and the layer stackup.

## Design state

The committed board routes clean: **0 DRC errors, 0 unconnected items, 0 schematic-parity issues**, 353 track segments and 57 vias. The remaining DRC output is 32 warnings, all cosmetic or library-hygiene (silkscreen clipped by the board edge, silkscreen overlap, footprint-library mismatches).

Before fabricating, verify the Molex connector pin numbering and polarization against the Fisker CON1 keying — that cannot be settled from the design files alone.

## License

Licensed under the [CERN Open Hardware Licence Version 2 - Strongly Reciprocal](LICENSE) (CERN-OHL-S-2.0).

## Disclaimer

This is a community hardware design shared as-is, with no warranty. It is designed specifically for the Fisker Ocean — using it on other platforms is unverified. **Use at your own risk.**
