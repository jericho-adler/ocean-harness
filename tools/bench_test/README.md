# Bench-test figure generator

Builds the annotated pictures in [`../../BENCH_TEST.md`](../../BENCH_TEST.md) from the KiCad 3D model.
Markers are placed from pad coordinates read out of `Ocean Harness.kicad_pcb`, not positioned by hand.

## Regenerating

From the repository root:

```bash
mkdir -p build/renders bench_test_images/steps
for side in top bottom; do
  kicad-cli pcb render --side $side --background transparent --quality basic \
    -w 2800 -h 2380 -o "build/renders/base_$side.png" "PCB Files/Ocean Harness.kicad_pcb"
done
python3 tools/bench_test/gen1.py && python3 tools/bench_test/gen2.py
```

`OH_RENDER_DIR` and `OH_STEPS_DIR` override the input and output directories.
Needs `pillow`, `numpy` and `kicad-cli`.

Note there is **no `--floor`** flag: that is what keeps the renders free of shadows.

## The PDF

```bash
python3 tools/bench_test/make_pdf.py
```

Converts `BENCH_TEST.md` to `BENCH_TEST.pdf` (A4) through headless Chrome, with the print stylesheet
living in `make_pdf.py`. Needs the `markdown` package and Chrome; by default it calls
`flatpak run com.google.Chrome`, and `OH_CHROME` overrides that with any binary or command. The
intermediate HTML is left in `build/bench_test.html` if you want to tweak the styling.

## Calibration

`fig.py` maps board millimetres to pixels with a linear fit per axis, stored in `_CAL`. Those numbers were
measured by rendering the board twice — once as-is, once with 1.6 mm filled silkscreen disks at
(85, 69), (168, 69), (127, 40) and (135, 106) — and taking the centroid of each difference blob. The fit
is good to about 0.05 mm.

**The mapping is tied to that exact render command and image size.** If you change the render resolution,
the camera, or the board outline, redo the calibration before trusting any marker position.
