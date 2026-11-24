#!/usr/bin/env python3
"""Render BENCH_TEST.md to BENCH_TEST.pdf via headless Chrome.

    python3 tools/bench_test/make_pdf.py          # from the repository root

Needs the `markdown` package and Google Chrome. Chrome is used through flatpak by
default (com.google.Chrome); set OH_CHROME to a binary or a full command instead.
"""
import os
import re
import shlex
import subprocess
import sys
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SRC = os.path.join(ROOT, 'BENCH_TEST.md')
BUILD = os.path.join(ROOT, 'build')
HTML = os.path.join(BUILD, 'bench_test.html')
PDF = os.path.join(ROOT, 'BENCH_TEST.pdf')
TITLE = 'Ocean Harness bench test'

CSS = """
@page { size: A4; margin: 15mm 13mm 16mm; }
* { box-sizing: border-box; }
body {
  font: 10.3pt/1.5 "DejaVu Sans", "Segoe UI", system-ui, sans-serif;
  color: #1a1c22; margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1 { font-size: 23pt; margin: 0 0 2mm; letter-spacing: -.2pt; }
h1 + p { color: #4a505e; font-size: 10pt; }
h2 {
  font-size: 15pt; margin: 9mm 0 3mm; padding-bottom: 1.6mm;
  border-bottom: 2.2px solid #1a1c22; break-after: avoid;
}
h2.pagebreak { break-before: page; }
h3 { font-size: 12pt; margin: 6mm 0 2mm; color: #10131a; break-after: avoid; }
h4 { font-size: 10.6pt; margin: 4mm 0 1.5mm; color: #2a2f3a; break-after: avoid; }
p, ul, ol, table { margin: 0 0 2.6mm; }
a { color: #1256a8; text-decoration: none; }
code {
  font-family: "DejaVu Sans Mono", monospace; font-size: .86em;
  background: #f1f3f7; padding: .5mm 1.1mm; border-radius: 2px;
}
pre {
  background: #f6f8fb; border: 1px solid #dde2ea; border-radius: 4px;
  padding: 2.6mm 3mm; overflow-x: auto; font-size: 8.6pt; break-inside: avoid;
}
pre code { background: none; padding: 0; }
img {
  display: block; width: 100%; height: auto; margin: 3mm 0 4mm;
  border: 1px solid #d7dce5; border-radius: 4px; break-inside: avoid;
}
h3 + p > img, h4 + p > img { break-before: avoid; }
table { border-collapse: collapse; width: 100%; font-size: 9.1pt; break-inside: avoid; }
th, td { border: 1px solid #ccd3df; padding: 1.5mm 2.2mm; text-align: left; vertical-align: top; }
th { background: #eef1f6; font-weight: 700; }
tbody tr:nth-child(even) { background: #fafbfd; }
blockquote {
  margin: 3mm 0; padding: 2.6mm 3.4mm; background: #fff8e8;
  border-left: 3.4px solid #e0a106; border-radius: 0 4px 4px 0; break-inside: avoid;
}
blockquote p { margin: 0; }
blockquote p + p { margin-top: 1.8mm; }
ul { padding-left: 5.4mm; break-inside: avoid; }
li { margin: .9mm 0; }
li.task { list-style: none; margin-left: -5.4mm; padding-left: 6.4mm; position: relative; }
li.task::before {
  content: ""; position: absolute; left: 0; top: .9mm; width: 3.4mm; height: 3.4mm;
  border: 1.4px solid #6b7384; border-radius: 1px; background: #fff;
}
hr { border: 0; border-top: 1px solid #dfe4ec; margin: 7mm 0; }
/* a rule immediately before a page break just leaves a blank page */
hr:has(+ h2.pagebreak) { display: none; margin: 0; }
strong { color: #0c0e14; }
.meta { color: #697086; font-size: 8.6pt; margin-top: 1.5mm; }
"""


def build_html():
    try:
        import markdown
    except ImportError:
        sys.exit('needs the markdown package:  python3 -m pip install markdown')

    text = open(SRC, encoding='utf-8').read()
    body = markdown.markdown(
        text, extensions=['tables', 'fenced_code', 'attr_list', 'sane_lists', 'md_in_html'])

    # python-markdown leaves "[ ]" literal; turn those into real checkboxes
    body = re.sub(r'<li>\s*\[ \]\s*', '<li class="task">', body)
    # page break before the big sections
    for h in ('Part 1: unpowered checks', 'Part 2: powered from the bench supply',
              'Pass criteria before it goes in the car'):
        body = body.replace(f'<h2>{h}</h2>', f'<h2 class="pagebreak">{h}</h2>')

    os.makedirs(BUILD, exist_ok=True)
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<title>{TITLE}</title><base href="{urllib.parse.quote(ROOT)}/">'
            f'<style>{CSS}</style></head><body>{body}</body></html>')
    open(HTML, 'w', encoding='utf-8').write(html)
    return HTML


def to_pdf(html_path):
    chrome = os.environ.get('OH_CHROME', 'flatpak run com.google.Chrome')
    cmd = shlex.split(chrome) + [
        '--headless', '--disable-gpu', '--no-sandbox', '--no-pdf-header-footer',
        '--virtual-time-budget=30000',
        f'--print-to-pdf={PDF}', 'file://' + urllib.parse.quote(html_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if not os.path.exists(PDF):
        sys.exit('chrome did not produce a PDF\n' + (r.stderr or r.stdout)[-2500:])
    return PDF


if __name__ == '__main__':
    out = to_pdf(build_html())
    print('wrote %s (%.1f MB)' % (out, os.path.getsize(out) / 1e6))
