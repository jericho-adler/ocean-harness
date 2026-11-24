"""Diagnostic close-up: where to concentrate the IPA clean.

SW_VCC and the ADAS CAN nets only come near each other at U1 and U2, so that is
where a residue path between them has to be.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig import Fig, COL

OUT = os.environ.get('OH_DIAG_DIR', 'bench_test_images/diagnostics')
os.makedirs(OUT, exist_ok=True)

# U1 is rotated -90, U2 +90, so their pin-1..4 rows face opposite ways
U1 = {1: (128.155, 94.776), 2: (126.885, 94.776), 3: (125.615, 94.776), 4: (124.345, 94.776),
      5: (124.345, 100.224), 6: (125.615, 100.224), 7: (126.885, 100.224), 8: (128.155, 100.224)}
U2 = {1: (118.345, 100.224), 2: (119.615, 100.224), 3: (120.885, 100.224), 4: (122.155, 100.224),
      5: (122.155, 94.776), 6: (120.885, 94.776), 7: (119.615, 94.776), 8: (118.345, 94.776)}
C3_SW = (124.475, 92.600)

f = Fig('top', '', 'Where to concentrate the IPA', [
    'Top side, magnified. SW_VCC and the ADAS CAN nets are only ever close at U1 and U2.',
    'Pin 4 is SW_VCC; pin 2 is the CAN line. Only pin 3 (GND) sits between them.'],
    legend_rows=5, zoom=(116.0, 90.0, 133.0, 103.5), zoom_w=1500)

# priority 1: U2 pins 2-3-4  (pin 19's net is U2 pin 2)
f.region(U2[2][0] - 0.9, U2[2][1] - 1.1, U2[4][0] + 0.9, U2[4][1] + 1.1, COL['pos'], pad=0.15, w=6)
f.pin(*U2[2], '2', COL['pos'], r=19, fs=24)
f.pin(*U2[3], '3', COL['gnd'], r=16, fs=22)
f.pin(*U2[4], '4', COL['meas'], r=19, fs=24)
f.callout(*U2[3], 'U2 pins 2-3-4  SCRUB HERE FIRST', COL['pos'], dx=-110, dy=150, fs=31)

# priority 2: U1 pins 2-3-4
f.region(U1[4][0] - 0.9, U1[4][1] - 1.1, U1[2][0] + 0.9, U1[2][1] + 1.1, COL['inspect'], pad=0.15, w=6)
f.pin(*U1[2], '2', COL['inspect'], r=17, fs=22)
f.pin(*U1[3], '3', COL['gnd'], r=15, fs=20)
f.pin(*U1[4], '4', COL['meas'], r=17, fs=22)
f.callout(*U1[3], 'U1 pins 2-3-4  then here', COL['inspect'], dx=120, dy=-150, fs=30)

f.pin(*C3_SW, '', COL['meas'], r=14)
f.callout(*C3_SW, 'C3 - SW_VCC, same net', COL['meas'], dx=-120, dy=-110, fs=27)

f.legend([
    (COL['pos'], 'U2 pin 2 is pin 19\'s net (ADAS_CAN_L_MOD). Pin 4 two pads away is SW_VCC.'),
    (COL['meas'], 'Pin 4 and pin 5 on both parts are SW_VCC - the 9 V that is getting onto the bus'),
    (COL['gnd'], 'Pin 3 is GND and sits between them, so the bridge has to span three pads'),
    (COL['inspect'], 'U1 is the same layout mirrored - do it too, its pin 8 reaches pin 19 through R4'),
    (COL['note'], 'Flood with IPA, work a stiff brush along the pin rows, flush again, dry fully.'),
])
f.save(os.path.join(OUT, 'diag_clean_targets.png'), width=1700)
