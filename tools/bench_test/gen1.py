import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig import *

OUT = os.environ.get('OH_STEPS_DIR', 'bench_test_images/steps')
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------- 1.1 visual
f = Fig('top', '1.1', 'Visual inspection', [
    'Top side, as the board sits in front of you. Nothing is powered.',
    'Check each circled part before you put any voltage on the board.'], legend_rows=4)
for x, y, t in [(153.0, 70.81, 'Q1'), (126.25, 97.5, 'U1'), (120.25, 97.5, 'U2')]:
    cx, cy, X0, Y0, X1, Y1 = f.region(x - 3.9, y - 2.8, x + 3.9, y + 2.8, COL['inspect'], pad=0.3)
f.callout(153.0, 67.9, 'Q1  pin 1 dot top-left, no bridges', COL['inspect'], dx=-170, dy=-205)
f.callout(119.5, 101.3, 'U1 / U2  pin 1 dots, no bridges', COL['inspect'], dx=-250, dy=120)
for x, y, t in [(157.9, 70.3, 'D15'), (135.5, 73.5, 'D13'), (129.5, 67.1, 'D12'),
                (124.25, 67.35, 'CR1'), (134.75, 98.25, 'D11'), (134.75, 91.0, 'D9')]:
    f.pin(x, y, '', COL['meas'], r=15)
f.callout(157.9, 68.2, 'D15 band matches the silk band', COL['meas'], dx=-150, dy=-120)
f.callout(134.75, 94.6, 'D9 / D11 / D12 / D13 / CR1: bands match silk', COL['meas'], dx=175, dy=120)
f.region(144.5, 71.6, 149.1, 73.9, COL['pos'], pad=0.3)
f.callout(145.0, 72.75, 'F1  3 A fuse fitted, not a 0 R link', COL['pos'], dx=-210, dy=-20)
f.region(121.7, 101.9, 132.6, 109.0, COL['comma'], pad=0.4)
f.callout(122.0, 106.5, 'J1 seated flat, 4 shell legs soldered', COL['comma'], dx=-175, dy=78)
f.legend([
    (COL['inspect'], 'Fine-pitch parts: look for solder bridges between adjacent pins'),
    (COL['meas'], 'Diodes: the cathode band must sit where the silkscreen band / * is'),
    (COL['pos'], 'F1 must be the real 3 A fuse - a link here removes the board\'s only fuse'),
    (COL['comma'], 'Connectors seated flat, no lifted pins, all four J1 shell legs wetted'),
])
f.save(f'{OUT}/step_1-1_visual.png')

# ------------------------------------------------------------ 1.2 rail shorts
f = Fig('top', '1.2', 'No shorts on the power rails', [
    'Ohms, black lead on any GND pad, red on each rail in turn. Readings climb as the caps charge.',
    'A reading under about 10 ohms is a short - find it before you apply power.'], legend_rows=3)
for k, lbl, col, dx, dy in [
        ('F1.2', 'VBAT_FUSED  (F1 right pad)', COL['pos'], 150, -150),
        ('C1.1', '12V_PROT  (C1, left pad)', COL['meas'], -150, 150),
        ('C2.1', 'VIN  (C2, left pad)', COL['meas'], 150, -140),
        ('C3.1', 'SW_VCC  (C3, left pad)', COL['meas'], -160, 130)]:
    x, y = PAD[k]
    f.pin(x, y, '', col, r=17)
    f.callout(x, y, lbl, col, dx=dx, dy=dy, fs=29)
for k in ('C1.2', 'C2.2', 'C3.2'):
    x, y = PAD[k]
    f.pin(x, y, '', COL['gnd'], r=13)
f.callout(*PAD['C2.2'], 'GND  (right pad of C1 / C2 / C3)', COL['gnd'], dx=150, dy=120, fs=29)
f.legend([
    (COL['pos'], 'VBAT_FUSED - expect OL or tens of kohms. Under 100 ohms is wrong.'),
    (COL['meas'], '12V_PROT / VIN / SW_VCC - expect a climbing kohm reading, never under 100 ohms'),
    (COL['gnd'], 'Black lead here. C1/C2/C3 all have GND on their right-hand pad.'),
])
f.save(f'{OUT}/step_1-2_rail_shorts.png')

# -------------------------------------------------- 1.3 passthrough section A
f = Fig('bottom', '1.3', 'Passthrough continuity - CON1 section A', [
    'Solder side, board flipped left-to-right: J3 (car harness) on the LEFT, J4 (ADAS ECU) on the RIGHT.',
    'Ohms from J3 pin n to J4 pin n. Every coloured pair must read under 1 ohm with the board unpowered.'],
    legend_rows=4)
for n in PASS_A:
    f.pair(J3[n], J4[n], COL['pass'])
for n in RELAY_A:
    f.pair(J3[n], J4[n], COL['relay'])
for n in PASS_A:
    f.pin(*J3[n], n, COL['pass'])
    f.pin(*J4[n], n, COL['pass'])
for n in RELAY_A:
    f.pin(*J3[n], n, COL['relay'])
    f.pin(*J4[n], n, COL['relay'])
for n in DEAD_A:
    f.pin(*J3[n], n, COL['dead'], r=17, fs=22)
    f.pin(*J4[n], n, COL['dead'], r=17, fs=22)
cx, cy, X0, Y0, X1, Y1 = f.region(120.09, 71.25, 127.71, 89.03, COL['relay'], pad=2.2)
f.callout(0, 0, 'K1 resting contacts carry pins 19 / 20', COL['relay'],
          dx=0, dy=-150, from_px=(cx, Y0))
f.callout(*J3[1], 'J3.1 = VBAT in', COL['pos'], dx=-150, dy=-40, fs=28)
f.callout(*J3[14], 'J3.14 = GND', COL['gnd'], dx=-150, dy=0, fs=28)
f.legend([
    (COL['pass'], '1, 6, 7, 14, 15, 16, 17, 18: straight passthrough - under 1 ohm'),
    (COL['relay'], '19, 20: ADAS CAN through K1\'s resting contacts - under 1 ohm. Open here means the '
                   'car loses its ADAS bus whenever the box is unpowered.'),
    (COL['dead'], 'Grey pins are not carried by this board - they must read open J3 to J4 (step 1.5)'),
    (COL['note'], 'Pin 1 is also where the bench supply goes in (step 2.2); pin 14 is board GND'),
])
f.save(f'{OUT}/step_1-3_passthrough_A.png')

# -------------------------------------------------- 1.4 passthrough section B
f = Fig('bottom', '1.4', 'Passthrough continuity - CON1 section B', [
    'Same solder-side view: J5 (car harness) on the LEFT, J6 (ADAS ECU) on the RIGHT.',
    'Section B is plain copper - no relay, no switches. Every coloured pair must read under 1 ohm.'],
    legend_rows=3)
for n in PASS_B:
    f.pair(J5[n], J6[n], COL['pass'])
for n in PASS_B:
    f.pin(*J5[n], n, COL['pass'])
    f.pin(*J6[n], n, COL['pass'])
for n in DEAD_B:
    f.pin(*J5[n], n, COL['dead'], r=17, fs=22)
    f.pin(*J6[n], n, COL['dead'], r=17, fs=22)
f.callout(*J5[1], 'MRR CAN L', COL['comma'], dx=-150, dy=40, fs=27)
f.callout(*J5[9], 'MRR CAN H  (tapped to J1, listen only)', COL['comma'], dx=-150, dy=-40, fs=27)
f.legend([
    (COL['pass'], '1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 15, 16: straight passthrough - under 1 ohm'),
    (COL['dead'], '6, 7, 8, 14: not carried - must read open J5 to J6'),
    (COL['comma'], 'Pins 1 and 9 (MRR CAN) also feed the listen-only tap to J1 - still under 1 ohm through'),
])
f.save(f'{OUT}/step_1-4_passthrough_B.png')
print('part 1a done')
