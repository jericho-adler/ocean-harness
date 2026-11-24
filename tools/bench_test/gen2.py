import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig import *

OUT = os.environ.get('OH_STEPS_DIR', 'bench_test_images/steps')
os.makedirs(OUT, exist_ok=True)

ALL_A = list(range(1, 21))
ALL_B = list(range(1, 17))


def supply(f, swapped=False, fs=30):
    """Mark the bench supply leads on J3.1 / J3.14."""
    pos, neg = (J3[14], J3[1]) if swapped else (J3[1], J3[14])
    f.pin(*pos, '+', COL['pos'], r=25, fs=30)
    f.pin(*neg, '-', COL['gnd'], r=25, fs=34)
    f.callout(*pos, ('RED to J3.14' if swapped else 'RED  +12 V  to J3.1'),
              COL['pos'], dx=-170, dy=-50, fs=fs)
    f.callout(*neg, ('BLACK to J3.1' if swapped else 'BLACK  -  to J3.14'),
              COL['gnd'], dx=-170, dy=50, fs=fs)


# ------------------------------------------------------- 1.5 isolation (bottom)
f = Fig('bottom', '1.5', 'Isolation - no car pin may touch the box supply', [
    'Still unpowered. Black lead on J3.14 (board GND), red on every other J3 / J5 pin in turn,',
    'then red on J3.1 (VBAT) and black on every other pin. Everything must read open.'],
    legend_rows=4)
for n in ALL_A:
    if n == 1:
        f.pin(*J3[n], n, COL['pos'])
    elif n == 14:
        f.pin(*J3[n], n, COL['gnd'])
    else:
        f.pin(*J3[n], n, COL['warn'])
for n in (1, 14):
    f.pin(*J4[n], n, COL['pos'] if n == 1 else COL['gnd'], r=17, fs=22)
f.callout(*J3[1], 'J3.1 VBAT', COL['pos'], dx=-160, dy=-30, fs=28)
f.callout(*J3[14], 'J3.14 GND', COL['gnd'], dx=-160, dy=30, fs=28)
f.callout(*J3[19], 'ADAS CAN pair: a few kohms to GND is normal (ESD array D3)',
          COL['warn'], dx=-160, dy=-120, fs=27)
f.legend([
    (COL['warn'], 'Every pin except 1 and 14: must read open (> 10 kohm) to both GND and VBAT'),
    (COL['pos'], 'Pin 1 is VBAT. It is deliberately shared with J4.1 - that pair is the ECU feed.'),
    (COL['gnd'], 'Pin 14 is board GND and is shared with J4.14. That is by design.'),
    (COL['note'], 'Also check the uncarried pins read open J3 to J4: 2, 3, 4, 5, 8, 9, 10, 11, 12, 13'),
])
f.save(f'{OUT}/step_1-5_isolation.png')

# --------------------------------------------- 1.6 no termination (bottom)
f = Fig('bottom', '1.6', 'No terminator across the car\'s CAN pair', [
    'Unpowered, measure across each ADAS CAN pair. The box must not load the car\'s bus when it is off.',
    'Measure both ways round - the ESD arrays make the reading polarity dependent.'], legend_rows=3)
f.pair(J3[19], J3[20], COL['warn'], w=6)
f.pair(J4[19], J4[20], COL['warn'], w=6)
for n in (19, 20):
    f.pin(*J3[n], n, COL['warn'])
    f.pin(*J4[n], n, COL['warn'])
f.callout(*J3[20], 'J3.19 - J3.20   car side', COL['warn'], dx=-170, dy=-70, fs=29)
f.callout(*J4[20], 'J4.19 - J4.20   ECU side', COL['warn'], dx=160, dy=-70, fs=29)
cx, cy, X0, Y0, X1, Y1 = f.region(129.5, 94.7, 132.0, 100.3, COL['meas'], pad=1.2)
f.callout(0, 0, 'R4 (120 ohm) must stay parked here', COL['meas'], dx=170, dy=120,
          from_px=(cx, Y1), fs=28)
f.legend([
    (COL['warn'], 'Both pairs: expect kohms or OL. About 120 ohms means R4 is across the bus - stop.'),
    (COL['meas'], 'R4 is only switched across the ECU pair when the box is powered AND SBU1 is high'),
    (COL['note'], 'A few kohms is fine: that is the PESD1CAN arrays, not a terminator'),
])
f.save(f'{OUT}/step_1-6_no_termination.png')

# ----------------------------------------------- 2.1 reverse polarity (bottom)
f = Fig('bottom', '2.1', 'Reverse polarity - do this first', [
    'Supply set to 12.0 V, current limit 50 mA, output OFF. Connect the leads BACKWARDS, then switch on',
    'for about two seconds and watch the current. Q1 should block it completely.'], legend_rows=3)
supply(f, swapped=True)
cx, cy, X0, Y0, X1, Y1 = f.region(149.3, 68.1, 156.7, 73.5, COL['meas'], pad=1.0)
f.callout(0, 0, 'Q1 sits here on the top side', COL['meas'], dx=150, dy=-120,
          from_px=(cx, Y0), fs=29)
f.legend([
    (COL['pos'], 'RED lead on J3.14 and BLACK on J3.1 - deliberately the wrong way round'),
    (COL['meas'], 'Expect about 0 mA. More than a few mA means Q1 is backwards or damaged - stop.'),
    (COL['note'], 'Switch off and put the leads back the right way before going on'),
])
f.save(f'{OUT}/step_2-1_reverse_polarity.png')

# ------------------------------------------------- 2.2 first power-up (bottom)
f = Fig('bottom', '2.2', 'First power-up', [
    'Leads the right way round now: 12.0 V, current limit 100 mA. Listen for K1 to click as it pulls in.',
    'Note that J4.1 also goes to 12 V - that is the ECU feed passing straight through, not a fault.'],
    legend_rows=4)
supply(f)
f.pin(*J4[1], '1', COL['pos'], r=21)
f.callout(*J4[1], 'J4.1 reads 12 V - expected', COL['pos'], dx=150, dy=-60, fs=28)
cx, cy, X0, Y0, X1, Y1 = f.region(120.09, 71.25, 127.71, 89.03, COL['relay'], pad=2.2)
f.callout(0, 0, 'K1 should click at about 10.5 V', COL['relay'], dx=0, dy=-150,
          from_px=(cx, Y0), fs=29)
f.legend([
    (COL['pos'], 'Expect about 11 mA at 12.0 V. Hitting the 100 mA limit means a short - switch off.'),
    (COL['relay'], 'K1 clicks in at roughly 10.5 V input and stays in while the box is powered'),
    (COL['note'], 'After a minute, flip the board and touch-test F1, Q1, R5 and K1 - warm is fine'),
    (COL['note'], 'J3.14 is the only ground reference you need for every voltage below'),
])
f.save(f'{OUT}/step_2-2_first_power_up.png')

# ---------------------------------------------------- 2.3 rails (top)
f = Fig('top', '2.3', 'Rail voltages under power', [
    'Powered at 12.0 V. Black lead on the GND pad of any of C1 / C2 / C3 (their right-hand pad).',
    'Each rail sits a fixed step below the one before it - that is R5 and R6 doing their job.'],
    legend_rows=4)
for k, lbl, dx, dy in [('F1.2', 'VBAT_FUSED   = supply voltage', 150, -150),
                       ('C1.1', '12V_PROT   12.0 V', -160, 150),
                       ('C2.1', 'VIN   10.3 V', 150, -140),
                       ('C3.1', 'SW_VCC   9.9 V', -165, 130)]:
    x, y = PAD[k]
    f.pin(x, y, '', COL['meas'], r=17)
    f.callout(x, y, lbl, COL['meas'], dx=dx, dy=dy, fs=29)
for k in ('C1.2', 'C2.2', 'C3.2'):
    f.pin(*PAD[k], '', COL['gnd'], r=13)
f.callout(*PAD['C2.2'], 'GND', COL['gnd'], dx=140, dy=115, fs=28)
f.legend([
    (COL['meas'], 'At 12.0 V in: 12V_PROT 12.0 V, VIN 10.3 V, SW_VCC 9.9 V (all within about 0.3 V)'),
    (COL['meas'], 'At 14.0 V in: 12V_PROT 14.0 V, VIN 12.0 V, SW_VCC 11.6 V'),
    (COL['warn'], 'SW_VCC must never exceed about 12.3 V - D13 clamps it above roughly 14.5 V in'),
    (COL['gnd'], 'Black lead on the right-hand pad of C1, C2 or C3'),
])
f.save(f'{OUT}/step_2-3_rails.png')

# ------------------------------------------------ 2.4 no backfeed (bottom)
f = Fig('bottom', '2.4', 'Nothing from the box drives a car pin', [
    'The key "will not hurt the car" check. Box powered at 12 V, nothing plugged into any connector.',
    'Measure each pin LOADED: hang 100 ohm from the pin to board GND and read the volts across it.'],
    legend_rows=4)
for n in ALL_A:
    c = COL['pos'] if n == 1 else (COL['gnd'] if n == 14 else COL['pass'])
    f.pin(*J3[n], n, c, r=19, fs=24)
    f.pin(*J4[n], n, c, r=19, fs=24)
for n in ALL_B:
    f.pin(*J5[n], n, COL['pass'], r=19, fs=24)
    f.pin(*J6[n], n, COL['pass'], r=19, fs=24)
f.callout(*J3[1], 'pin 1 = 12 V, expected', COL['pos'], dx=-165, dy=-30, fs=27)
f.callout(*J3[14], 'pin 14 = 0 V, it is GND', COL['gnd'], dx=-165, dy=30, fs=27)
f.legend([
    (COL['pass'], 'Every green pin must read under 0.2 V with the 100 ohm load fitted. Bare they '
                  'float and show several volts of pickup - that alone is not a fault.'),
    (COL['pos'], 'Pin 1 on J3 and J4 reads your supply voltage. That is the deliberate ECU feed.'),
    (COL['gnd'], 'Pin 14 on J3 and J4 is board GND and reads 0 V'),
    (COL['note'], '100 ohm emulates the bus: volts on the bus = reading x 0.6. Near a volt is a real '
                  'source - that is the fail. Repeat with SBU1 high (step 2.6).'),
])
f.save(f'{OUT}/step_2-4_no_backfeed.png')

# ------------------------------------------- 2.5 relay switchover (bottom)
f = Fig('bottom', '2.5', 'Relay switchover and release', [
    'Box powered. K1 has moved the car\'s ADAS pair away from the ECU and onto the comma side.',
    'This is the proof that the car gets its bus back the moment the box loses power.'], legend_rows=4)
for n in (19, 20):
    f.pin(*J3[n], n, COL['relay'])
    f.pin(*J4[n], n, COL['comma'])
f.pair(J3[19], K1[8], COL['meas'], w=5)
f.pair(J3[20], K1[9], COL['meas'], w=5)
f.pin(*K1[8], '8', COL['meas'])
f.pin(*K1[9], '9', COL['meas'])
f.callout(*K1[9], 'K1.9 = ADAS_CAN_H_C', COL['meas'], dx=150, dy=-130, fs=28)
f.callout(*K1[8], 'K1.8 = ADAS_CAN_L_C', COL['meas'], dx=-150, dy=130, fs=28)
f.callout(*J3[20], 'J3.19 / 20  car side', COL['relay'], dx=-165, dy=-60, fs=28)
f.callout(*J4[20], 'J4.19 / 20  ECU side', COL['comma'], dx=155, dy=-60, fs=28)
f.legend([
    (COL['meas'], 'Powered: J3.20 to K1.9 and J3.19 to K1.8 both read under 1 ohm'),
    (COL['relay'], 'Powered: J3.19 to J4.19 now reads OPEN - the car is routed to the comma port'),
    (COL['comma'], 'J4.19 / 20 stay wired to J1 B3 / B2 whatever the relay is doing'),
    (COL['note'], 'Power OFF: J3.19 to J4.19 must return to under 1 ohm. This is the fail-safe.'),
])
f.save(f'{OUT}/step_2-5_relay_switchover.png')

# ------------------------------------------ 2.6a SBU1 injection (top)
f = Fig('top', '2.6a', 'Driving SBU1 to open the bridge', [
    'SBU1 is the comma device\'s control line. On the bench, drive it from a 3.3 V or 5 V source',
    'referenced to board GND. R2\'s upper pad is the only accessible point on that net.'], legend_rows=3)
x, y = PAD['R2.1']
f.pin(x, y, '', COL['pos'], r=16)
f.callout(x, y, 'R2 upper pad = SBU1   inject 3.3-5 V here', COL['pos'], dx=150, dy=-150, fs=29)
f.pin(*PAD['R3.2'], '', COL['gnd'], r=14)
f.callout(*PAD['R3.2'], 'R3 lower pad = GND', COL['gnd'], dx=150, dy=130, fs=28)
for k in ('U1', 'U2'):
    cx, cy, X0, Y0, X1, Y1 = f.region(PAD[k][0] - 3.0, PAD[k][1] - 3.8,
                                      PAD[k][0] + 3.0, PAD[k][1] + 3.8, COL['meas'], pad=0.3)
f.callout(0, 0, 'U1 / U2 - the analog switches that open', COL['meas'], dx=-140, dy=165,
          from_px=(cx, Y1), fs=28)
f.region(129.3, 97.8, 132.7, 99.2, COL['warn'], pad=0.4)
f.callout(131.0, 98.5, 'R4 120 ohm terminator', COL['warn'], dx=160, dy=60, fs=28)
f.legend([
    (COL['pos'], 'SBU1 low or floating is the safe default: R2 + R3 pull it to GND through 240 ohms'),
    (COL['meas'], 'SBU1 high opens the U1 / U2 bridge and cuts the car from the ECU'),
    (COL['warn'], 'SBU1 high also switches R4 across the ECU-side pair as its terminator'),
])
f.save(f'{OUT}/step_2-6a_sbu1_inject.png')

# ------------------------------------------ 2.6b SBU1 measure (bottom)
f = Fig('bottom', '2.6b', 'What SBU1 should change', [
    'Box powered. Measure on the solder side while you toggle SBU1 between 0 V and 3.3 V.',
    'Low = car and ECU still joined through the switches. High = cut, with R4 terminating the ECU side.'],
    legend_rows=4)
for n in (19, 20):
    f.pin(*J4[n], n, COL['comma'])
f.pair(J4[19], K1[8], COL['meas'], w=5)
f.pair(J4[20], K1[9], COL['meas'], w=5)
f.pair(J4[19], J4[20], COL['warn'], w=6)
f.pin(*K1[8], '8', COL['meas'])
f.pin(*K1[9], '9', COL['meas'])
f.callout(*J4[20], 'J4.19 - J4.20', COL['warn'], dx=160, dy=-80, fs=28)
f.callout(*K1[9], 'K1.9 / K1.8 = comma side', COL['meas'], dx=150, dy=-130, fs=28)
f.legend([
    (COL['meas'], 'SBU1 LOW:  J4.19 to K1.8 and J4.20 to K1.9 read about 11-18 ohms (one switch on)'),
    (COL['warn'], 'SBU1 HIGH: those go OPEN, and J4.19 to J4.20 reads about 131-138 ohms (R4)'),
    (COL['comma'], 'Both states are normal. Low is what the board does with no comma device attached.'),
    (COL['note'], 'Then redo step 2.4 with SBU1 high - no car pin may sit at 12 V in either state'),
])
f.save(f'{OUT}/step_2-6b_sbu1_measure.png')
print('part 2 done')
