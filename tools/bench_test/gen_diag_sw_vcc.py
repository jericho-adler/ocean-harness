"""Diagnostic figure: is the 9 V on J3/J4 pin 19 coming from SW_VCC?

Two panels stitched side by side - where to put the load, and where to read.
Run exactly like gen1/gen2 (see README).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from fig import Fig, COL, font, J3, J4, K1, PAD, INK, GREY

OUT = os.environ.get('OH_DIAG_DIR', 'bench_test_images/diagnostics')
os.makedirs(OUT, exist_ok=True)
TMP = os.environ.get('OH_RENDER_DIR', 'build/renders')

# ------------------------------------------------- panel A: where the load goes
a = Fig('bottom', 'A', 'Put the load here', [
    'Solder side. Clip a 10 kohm resistor between J3 pin 19 and J3 pin 14 (GND) and leave it there.',
    'Pin 19 and pin 14 are both in J3\'s left-hand column, four pads apart.'], legend_rows=3)
a.pin(*J3[19], '19', COL['meas'], r=25, fs=28)
a.pin(*J3[14], '14', COL['gnd'], r=25, fs=28)
a.pair(J3[19], J3[14], COL['meas'], w=7)
a.callout(*J3[19], '10 kohm from here...', COL['meas'], dx=-165, dy=-80, fs=30)
a.callout(*J3[14], '...to here (GND)', COL['gnd'], dx=-165, dy=80, fs=30)
a.pin(*J4[19], '19', COL['comma'], r=19, fs=24)
a.callout(*J4[19], 'J4.19 is the same node when powered', COL['comma'], dx=150, dy=70, fs=27)
a.legend([
    (COL['meas'], 'J3 pin 19 - the pin showing 9 V. Left-hand column, 5 pads up from pin 14.'),
    (COL['gnd'], 'J3 pin 14 - board GND. The resistor goes between these two and stays there.'),
    (COL['comma'], 'With the box powered J4.19 is the same net, so either pin works'),
])
pa = a.save(os.path.join(TMP, '_diagA.png'), width=1500) or os.path.join(TMP, '_diagA.png')

# ------------------------------------------------- panel B: where to read
b = Fig('top', 'B', 'Watch SW_VCC here', [
    'Top side. Read C3\'s LEFT pad against its right pad (GND), with the load off pin 19 and then on.',
    'If SW_VCC sags when the load goes on, U1 is feeding the bus. If it does not move, it is leakage.'],
    legend_rows=4)
x, y = PAD['C3.1']
b.pin(x, y, '', COL['pos'], r=18)
b.callout(x, y, 'SW_VCC   C3 left pad', COL['pos'], dx=-165, dy=-130, fs=30)
b.pin(*PAD['C3.2'], '', COL['gnd'], r=15)
b.callout(*PAD['C3.2'], 'GND   C3 right pad', COL['gnd'], dx=150, dy=-60, fs=29)
cx, cy, X0, Y0, X1, Y1 = b.region(PAD['U1'][0] - 3.0, PAD['U1'][1] - 3.8,
                                  PAD['U1'][0] + 3.0, PAD['U1'][1] + 3.8, COL['warn'], pad=0.3)
b.callout(0, 0, 'U1 - the suspect', COL['warn'], dx=-150, dy=150, from_px=(cx, Y1), fs=29)
b.pin(*PAD['R4.1'], '', COL['check'] if 'check' in COL else COL['inspect'], r=15)
b.callout(*PAD['R4.1'], 'R4 left pad - 9 V here too means it is U1', COL['inspect'], dx=150, dy=120, fs=28)
b.legend([
    (COL['pos'], 'SW_VCC unloaded sits at about 9.9 V with 12.0 V going in'),
    (COL['warn'], 'Drops to roughly 7.4 V when you load pin 19  ->  U1 is leaking onto the bus'),
    (COL['gnd'], 'Stays at 9.9 V and does not budge  ->  high-impedance leakage, clean the board'),
    (COL['inspect'], 'R4 is 120 ohms from U1 pin 8 to pin 19\'s net - that is the path if U1 is bad'),
])
pb = b.save(os.path.join(TMP, '_diagB.png'), width=1500) or os.path.join(TMP, '_diagB.png')

# ------------------------------------------------------------------ stitch
A, B = Image.open(os.path.join(TMP, '_diagA.png')), Image.open(os.path.join(TMP, '_diagB.png'))
HEAD, GAP, PAD_ = 150, 36, 36
W = A.width + B.width + GAP + 2 * PAD_
H = HEAD + max(A.height, B.height) + PAD_
s = Image.new('RGB', (W, H), (255, 255, 255))
d = ImageDraw.Draw(s)
d.text((PAD_, 34), 'Diagnostic', font=font(52), fill=GREY)
w = d.textlength('Diagnostic  ', font=font(52))
d.text((PAD_ + w, 34), 'Is the 9 V on pin 19 coming from SW_VCC?', font=font(52), fill=INK)
d.text((PAD_, 100), 'Box powered at 12.0 V. Do A first and leave the resistor fitted, then read B with it '
                    'off and on.', font=font(30, False), fill=(66, 72, 84))
s.paste(A, (PAD_, HEAD))
s.paste(B, (PAD_ + A.width + GAP, HEAD))
d.line([PAD_ + A.width + GAP // 2, HEAD, PAD_ + A.width + GAP // 2, HEAD + max(A.height, B.height)],
       fill=(214, 219, 228), width=3)
out = os.path.join(OUT, 'diag_sw_vcc.png')
s.save(out, optimize=True)
for f in ('_diagA.png', '_diagB.png'):
    os.remove(os.path.join(TMP, f))
print('wrote', out, s.size)
