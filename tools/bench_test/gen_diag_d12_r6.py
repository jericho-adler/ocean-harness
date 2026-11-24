"""Diagnostic close-up: is D12 shorted, reversed, or is R6 the problem?

Zoomed top-side view of the SW_VCC supply chain. Run like the other generators.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig import Fig, COL

OUT = os.environ.get('OH_DIAG_DIR', 'bench_test_images/diagnostics')
os.makedirs(OUT, exist_ok=True)

D12_A = (128.10, 67.10)   # left pad, anode, VIN
D12_K = (130.90, 67.10)   # right pad, cathode, SW_IN
R6_L = (131.68, 72.25)    # SW_IN
R6_R = (133.32, 72.25)    # SW_VCC
C2_L = (131.22, 74.75)    # VIN
D13_K = (135.50, 75.22)   # SW_VCC

f = Fig('top', '', 'D12 and R6 close-up', [
    'Top side, magnified. Board UNPOWERED for both tests below.',
    'Measure across each part\'s OWN two pads, not through the chain.'],
    legend_rows=5, zoom=(124.0, 62.5, 140.0, 79.0), zoom_w=1460)

f.pin(*D12_A, '', COL['pos'], r=17)
f.pin(*D12_K, '', COL['meas'], r=17)
f.callout(*D12_A, 'D12 LEFT = anode, on VIN', COL['pos'], dx=-120, dy=-150, fs=30)
f.callout(*D12_K, 'D12 RIGHT = cathode, on SW_IN', COL['meas'], dx=130, dy=-150, fs=30)

f.pin(*R6_L, '', COL['meas'], r=17)
f.pin(*R6_R, '', COL['pass'], r=17)
f.callout(*R6_L, 'R6 LEFT = SW_IN', COL['meas'], dx=-130, dy=100, fs=30)
f.callout(*R6_R, 'R6 RIGHT = SW_VCC', COL['pass'], dx=140, dy=60, fs=30)

f.pin(*C2_L, '', COL['dead'], r=13)
f.callout(*C2_L, 'C2 left = VIN', COL['dead'], dx=-130, dy=120, fs=27)
f.pin(*D13_K, '', COL['dead'], r=13)
f.callout(*D13_K, 'D13 top = SW_VCC', COL['dead'], dx=120, dy=120, fs=27)

f.legend([
    (COL['pos'], 'TEST 1 - diode mode across D12 only. Red on LEFT, black on RIGHT: expect 0.2-0.3 V.'),
    (COL['meas'], '   Reverse it: expect OL. Both low = shorted. Both OL = open. Low on the REVERSE '
                  'direction only = fitted backwards.'),
    (COL['pass'], 'TEST 2 - ohms across R6 only, left pad to right pad: expect 3.3 kohm.'),
    (COL['dead'], 'Do not measure VIN to SW_VCC through the chain - C2 and C3 make that reading drift.'),
    (COL['warn'], 'Discharge between readings: short each part\'s pads together briefly before reversing.'),
])
f.save(os.path.join(OUT, 'diag_d12_r6.png'), width=1700)
