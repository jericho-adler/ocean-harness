"""Annotated bench-test figures for the Ocean Harness board.

Base images are KiCad 3D renders made with exactly:
    kicad-cli pcb render --side {top|bottom} --background transparent \
        --quality basic -w 2800 -h 2380
The mm -> pixel map was derived by diffing those renders against renders of the
same board carrying 1.6 mm silkscreen disks at four known coordinates.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S = os.environ.get('OH_RENDER_DIR', 'build/renders')

# marker (mm, px) pairs from the calibration diff, image 2776 x 2352
_CAL = {
    'top':    {'x': [(127, 1393.63), (168, 2452.27), (85, 311.19), (135, 1599.79)],
               'y': [(40, 316.45), (69, 1061.72), (69, 1063.41), (106, 2017.00)]},
    'bottom': {'x': [(127, 1380.76), (85, 2463.31), (168, 322.30), (135, 1174.68)],
               'y': [(40, 316.45), (69, 1061.70), (69, 1063.40), (106, 2017.02)]},
}


def _fit(pairs):
    m = np.array([p[0] for p in pairs], float)
    p = np.array([p[1] for p in pairs], float)
    (s, o), *_ = np.linalg.lstsq(np.vstack([m, np.ones_like(m)]).T, p, rcond=None)
    return s, o


XF = {k: {a: _fit(v) for a, v in d.items()} for k, d in _CAL.items()}

INK = (24, 26, 32)
GREY = (122, 130, 142)
BG = (255, 255, 255)

COL = {
    'pos':    (214, 40, 40),      # +12 V
    'gnd':    (40, 44, 52),       # ground / black lead
    'pass':   (26, 164, 90),      # straight passthrough
    'relay':  (240, 138, 20),     # through relay contacts
    'meas':   (0, 132, 222),      # measure here
    'warn':   (170, 60, 210),     # must be open / must NOT read
    'inspect': (226, 106, 0),
    'dead':   (150, 156, 166),    # not connected / not used
    'comma':  (0, 168, 184),      # comma-side nets
    'note':   (72, 80, 96),       # legend rows that are an instruction, not a marker
}

_F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'


def font(sz, bold=True):
    try:
        return ImageFont.truetype(_F % ('-Bold' if bold else ''), sz)
    except OSError:
        return ImageFont.load_default()


class Fig:
    MARGIN = 60

    def __init__(self, side, step, title, subs=(), legend_rows=0, zoom=None, zoom_w=1500):
        """zoom = (x0, y0, x1, y1) in board mm; crops and scales to that region."""
        base = Image.open(f'{S}/base_{side}.png').convert('RGBA')
        self.side = side
        self._scale = 1.0
        if zoom:
            sx, ox = XF[side]['x']
            sy, oy = XF[side]['y']
            xa, xb = sorted([sx * zoom[0] + ox, sx * zoom[2] + ox])
            ya, yb = sorted([sy * zoom[1] + oy, sy * zoom[3] + oy])
            x0, y0, x1, y1 = int(xa), int(ya), int(xb), int(yb)
            board = base.crop((x0, y0, x1, y1))
            self._scale = zoom_w / board.width
            board = board.resize((zoom_w, round(board.height * self._scale)), Image.LANCZOS)
        else:
            a = np.array(base)[:, :, 3]
            ys, xs = np.where(a > 8)
            x0, x1 = xs.min() - 12, xs.max() + 12
            y0, y1 = ys.min() - 12, ys.max() + 12
            board = base.crop((x0, y0, x1, y1))
        self._ox, self._oy = x0, y0

        head = 250 if subs else 190
        foot = 40 + legend_rows * 62 + (34 if legend_rows else 0)
        W = board.width + 2 * self.MARGIN
        H = head + board.height + foot
        self.img = Image.new('RGB', (W, H), BG)
        self.img.paste(board, (self.MARGIN, head), board)
        self.d = ImageDraw.Draw(self.img, 'RGBA')
        self.W, self.H, self.head, self.foot = W, H, head, foot

        if step:
            self.d.text((self.MARGIN, 44), f'Step {step}', font=font(62), fill=GREY)
            w = self.d.textlength(f'Step {step}  ', font=font(62))
        else:
            w = 0
        self.d.text((self.MARGIN + w, 44), title, font=font(62), fill=INK)
        yy = 128
        for s in subs:
            self.d.text((self.MARGIN, yy), s, font=font(34, False), fill=(66, 72, 84))
            yy += 44
        self._legend_y = head + board.height + 26

    # ----------------------------------------------------------- geometry
    def px(self, x, y):
        sx, ox = XF[self.side]['x']
        sy, oy = XF[self.side]['y']
        return ((sx * x + ox - self._ox) * self._scale + self.MARGIN,
                (sy * y + oy - self._oy) * self._scale + self.head)

    @property
    def ppmm(self):
        return abs(XF[self.side]['x'][0]) * self._scale

    # ----------------------------------------------------------- elements
    def pin(self, x, y, text, color, r=21, fs=26):
        cx, cy = self.px(x, y)
        self.d.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], fill=(255, 255, 255, 235))
        self.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,))
        if text:
            self.d.text((cx, cy + 1), str(text), font=font(fs), fill=(255, 255, 255), anchor='mm')
        return cx, cy

    def pair(self, p, q, color, w=3):
        ax, ay = self.px(*p)
        bx, by = self.px(*q)
        self.d.line([ax, ay, bx, by], fill=color + (190,), width=w)

    def region(self, x0, y0, x1, y1, color, pad=1.0, w=5, dash=26):
        ax, ay = self.px(x0 - pad, y0 - pad)
        bx, by = self.px(x1 + pad, y1 + pad)
        X0, X1 = sorted((ax, bx))
        Y0, Y1 = sorted((ay, by))
        for (sx, sy, ex, ey) in ((X0, Y0, X1, Y0), (X1, Y0, X1, Y1),
                                 (X1, Y1, X0, Y1), (X0, Y1, X0, Y0)):
            n = max(1, int(math.hypot(ex - sx, ey - sy) / dash))
            for i in range(0, n, 2):
                t0, t1 = i / n, min(1, (i + 1) / n)
                self.d.line([sx + (ex - sx) * t0, sy + (ey - sy) * t0,
                             sx + (ex - sx) * t1, sy + (ey - sy) * t1],
                            fill=color + (255,), width=w)
        return (X0 + X1) / 2, (Y0 + Y1) / 2, X0, Y0, X1, Y1

    def chip(self, px, py, text, color, anchor='mm', fs=30):
        f = font(fs)
        l, t, r, b = self.d.textbbox((px, py), text, font=f, anchor=anchor)
        self.d.rounded_rectangle([l - 16, t - 11, r + 16, b + 11], radius=9,
                                 fill=(255, 255, 255, 248), outline=color + (255,), width=4)
        self.d.text((px, py), text, font=f, fill=INK, anchor=anchor)

    def callout(self, x, y, text, color, dx=140, dy=-120, fs=30, from_px=None):
        cx, cy = from_px or self.px(x, y)
        tx, ty = cx + dx, cy + dy
        # keep the text chip inside the canvas
        anchor = 'lm' if dx >= 0 else 'rm'
        l, _, r, _ = self.d.textbbox((tx, ty), text, font=font(fs), anchor=anchor)
        lim = self.MARGIN - 8
        if l - 18 < lim:
            tx += lim - (l - 18)
        if r + 18 > self.W - lim:
            tx -= (r + 18) - (self.W - lim)
        ty = min(max(ty, self.head + 26), self.head + self.H - self.head - self.foot - 26)
        self.d.line([cx, cy, tx, ty], fill=(255, 255, 255, 235), width=10)
        self.d.line([cx, cy, tx, ty], fill=color + (255,), width=4)
        self.chip(tx, ty, text, color, 'lm' if dx >= 0 else 'rm', fs)

    def arrow(self, p, q, color, w=11):
        ax, ay = self.px(*p)
        bx, by = self.px(*q)
        self.d.line([ax, ay, bx, by], fill=(255, 255, 255, 230), width=w + 8)
        self.d.line([ax, ay, bx, by], fill=color + (255,), width=w)
        a = math.atan2(by - ay, bx - ax)
        for s in (0.45, -0.45):
            self.d.line([bx, by, bx - 40 * math.cos(a - s), by - 40 * math.sin(a - s)],
                        fill=color + (255,), width=w)

    def legend(self, items):
        yy = self._legend_y
        avail = self.W - self.MARGIN - (self.MARGIN + 54)
        for color, txt in items:
            fs = 32
            while fs > 18 and self.d.textlength(txt, font=font(fs, False)) > avail:
                fs -= 1
            self.d.ellipse([self.MARGIN, yy + 4, self.MARGIN + 34, yy + 38], fill=color + (255,))
            self.d.text((self.MARGIN + 54, yy + 5), txt, font=font(fs, False), fill=INK)
            yy += 62

    def save(self, path, width=2000):
        im = self.img
        if width and width < im.width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(path, optimize=True)
        print('  wrote', path, im.size)


# ------------------------------------------------------------------ board data
J3 = {1: (139.299, 103.012), 6: (139.299, 90.312), 7: (139.299, 87.772),
      14: (141.839, 95.392), 15: (141.839, 92.852), 16: (141.839, 90.312),
      17: (141.839, 87.772), 18: (141.839, 85.232), 19: (141.839, 82.692),
      20: (141.839, 80.152), 2: (139.299, 100.472), 3: (139.299, 97.932),
      4: (139.299, 95.392), 5: (139.299, 92.852), 8: (139.299, 85.232),
      9: (139.299, 82.692), 10: (139.299, 80.152), 11: (141.839, 103.012),
      12: (141.839, 100.472), 13: (141.839, 97.932)}
J4 = {1: (114.535, 80.152), 6: (114.535, 92.852), 7: (114.535, 95.392),
      14: (111.995, 87.772), 15: (111.995, 90.312), 16: (111.995, 92.852),
      17: (111.995, 95.392), 18: (111.995, 97.932), 19: (111.995, 100.472),
      20: (111.995, 103.012), 2: (114.535, 82.692), 3: (114.535, 85.232),
      4: (114.535, 87.772), 5: (114.535, 90.312), 8: (114.535, 97.932),
      9: (114.535, 100.472), 10: (114.535, 103.012), 11: (111.995, 80.152),
      12: (111.995, 82.692), 13: (111.995, 85.232)}
J5 = {1: (139.299, 61.468), 9: (141.839, 61.468), 2: (139.299, 58.928),
      3: (139.299, 56.388), 4: (139.299, 53.848), 5: (139.299, 51.308),
      6: (139.299, 48.768), 7: (139.299, 46.228), 8: (139.299, 43.688),
      10: (141.839, 58.928), 11: (141.839, 56.388), 12: (141.839, 53.848),
      13: (141.839, 51.308), 14: (141.839, 48.768), 15: (141.839, 46.228),
      16: (141.839, 43.688)}
J6 = {1: (114.535, 43.688), 9: (111.995, 43.688), 2: (114.535, 46.228),
      3: (114.535, 48.768), 4: (114.535, 51.308), 5: (114.535, 53.848),
      6: (114.535, 56.388), 7: (114.535, 58.928), 8: (114.535, 61.468),
      10: (111.995, 46.228), 11: (111.995, 48.768), 12: (111.995, 51.308),
      13: (111.995, 53.848), 14: (111.995, 56.388), 15: (111.995, 58.928),
      16: (111.995, 61.468)}
K1 = {1: (120.090, 71.250), 4: (120.090, 78.870), 6: (120.090, 83.950),
      8: (120.090, 89.030), 9: (127.710, 89.030), 11: (127.710, 83.950),
      13: (127.710, 78.870), 16: (127.710, 71.250)}
J1B = {1: (129.900, 103.995), 2: (129.500, 104.694), 3: (128.700, 104.694),
       4: (128.300, 103.995), 9: (125.900, 103.995), 12: (124.300, 103.995)}
J1_SHELL = [(122.500, 104.745), (122.500, 107.745), (131.700, 104.745), (131.700, 107.745)]

# component pads used as measurement points (top side)
PAD = {
    'F1.1': (145.400, 72.750), 'F1.2': (148.200, 72.750),
    'Q1.D': (150.525, 70.175), 'Q1.S': (155.475, 71.445), 'Q1.G': (155.475, 68.905),
    'C1.1': (130.225, 100.500), 'C1.2': (131.775, 100.500),
    'C2.1': (131.225, 74.750), 'C2.2': (132.775, 74.750),
    'C3.1': (124.475, 92.600), 'C3.2': (126.025, 92.600),
    'R5.1': (135.662, 86.000), 'R5.2': (133.838, 86.000),
    'R2.1': (130.250, 96.075), 'R3.2': (131.250, 90.925),
    'R4.1': (130.175, 98.500), 'R4.2': (131.825, 98.500),
    'D15.K': (157.900, 72.025), 'D13.1': (135.500, 75.225),
    'U1': (126.25, 97.5), 'U2': (120.25, 97.5),
}

PASS_A = [1, 6, 7, 14, 15, 16, 17, 18]          # J3 <-> J4 straight
RELAY_A = [19, 20]                               # J3 <-> J4 through K1 NC
DEAD_A = [2, 3, 4, 5, 8, 9, 10, 11, 12, 13]
PASS_B = [1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 15, 16]
DEAD_B = [6, 7, 8, 14]
