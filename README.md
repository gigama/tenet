# tenet

Stochastic Hilbert Curve Generator

## QuickStart

**Hilbert mapping logic**
- `d2xy(level, d)` converts a 1-D index `d ∈ [0, 4^L)` to `(x, y)` on a `2^L × 2^L` grid using the standard recursive rotation/reflection algorithm.
- `col1` is linearly normalised to `[0, 4^L − 1]` and col2 is interpolated onto every grid cell with `np.interp`. Input points don't need to be evenly spaced or dense — sparse data interpolates gracefully.
- The curve is rendered as a `LineCollection` where each segment's colour is the mean of its two endpoint values, giving a smooth gradient along the path.

**CLI flags**

| Flag | Default | Notes |
|------|---------|-------|
| `input` (positional) | — | file path or `-` for stdin |
| `-l / --level` | `6` | 1–10; levels > 10 are refused |
| `-o / --output` | `hilbert_curve` | filename stem, no extension |
| `-f / --format` | `png` | `pdf` or `png` |
| `--dpi` | `300` | applied to PNG; ignored by PDF |
| `--cmap` | `viridis` | any matplotlib colormap |
| `--lw` | auto | auto-scaled as `1.6 − 0.18 × level` |
| `--title` | auto | custom title string |
| `--demo` | off | ignores input, uses built-in signal |

## Overview

**tenet.py** maps a one-dimensional stochastic signal onto a two-dimensional
[Hilbert space-filling curve](https://en.wikipedia.org/wiki/Hilbert_curve),
producing a colour-coded plot that exposes local structure and variance in data
that would otherwise appear as a flat time-series.

The name is a nod to the self-similar, reversible nature of space-filling
curves: a Hilbert curve can be traversed forwards *or* backwards, and at every
level of recursion it tiles itself — a tenet of its construction.

---

## Table of Contents

1. [Why a Hilbert curve?](#why-a-hilbert-curve)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Input format](#input-format)
5. [Usage](#usage)
6. [Command-line reference](#command-line-reference)
7. [Examples](#examples)
8. [Code walkthrough](#code-walkthrough)
9. [Performance notes](#performance-notes)
10. [Limitations](#limitations)

---

## Why a Hilbert curve?

A Hilbert curve is a *space-filling* curve: at level *L* it visits every cell
of a 2^L × 2^L grid exactly once, in an order that preserves locality — points
that are close in 1-D remain close in 2-D.  This makes it a natural canvas for
visualising a long stochastic signal:

* **Patterns become spatial.** Runs of high or low values cluster into visible
  regions instead of being smeared across a linear axis.
* **Scale is explicit.** The grid resolution is set by `--level`; increasing
  the level by 1 quadruples the number of cells, letting you zoom into finer
  structure.
* **Colour encodes value.** Any matplotlib colormap can be used to map the
  signal's range onto hue, making outliers and gradients immediately visible.

---

## Requirements

| Package | Tested version | Purpose |
|---------|---------------|---------|
| Python  | ≥ 3.10        | f-strings, `match`, type-union hints |
| NumPy   | ≥ 1.24        | Array maths, interpolation |
| Matplotlib | ≥ 3.7     | Rendering, `LineCollection`, colormaps |

No additional dependencies are needed.

---

## Installation

### 1 — Clone or download

```bash
git clone https://github.com/gigama/tenet.git
cd tenet
```

Or simply download `tenet.py` on its own.

### 2 — Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 3 — Install dependencies

```bash
pip install numpy matplotlib
```

### 4 — Make the script executable (Linux / macOS)

```bash
chmod +x tenet.py
```

You can then run it as `./tenet.py` instead of `python tenet.py`.

---

## Input format

The program reads a **two-column plain-text file** (or standard input).

| Column | Name | Range | Description |
|--------|------|-------|-------------|
| 1 | position | [0, MAX] | Position along the signal axis (time, distance, index, …) |
| 2 | value | (−∞, +∞) | Observed value at that position |

**Rules:**

* Columns may be separated by any whitespace or by commas.
* Lines beginning with `#` are treated as comments and skipped.
* Rows do not need to be sorted; the program sorts by `col1` internally.
* `col1` values must be finite and not all identical.
* `col2` values may be any real number, including negative values.
* There is no required minimum number of rows, but very sparse data (fewer
  rows than curve cells) will produce heavily interpolated output.

**Example file (`data.txt`):**

```
# time    signal
0.00      0.312
0.25     -1.047
0.50      2.891
0.75      0.003
1.00     -0.555
```

---

## Usage

```
python tenet.py [input] [options]
```

`input` may be a file path, `-` to read from standard input, or omitted when
`--demo` is supplied.

---

## Command-line reference

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `input` | — | positional | stdin | Input file path, or `-` for stdin |
| `--level` | `-l` | int | `6` | Hilbert curve level, 1–10 (side = 2^level) |
| `--output` | `-o` | str | `tenet` | Output filename stem (no extension) |
| `--format` | `-f` | choice | `png` | Output format: `png` or `pdf` |
| `--dpi` | — | int | `300` | PNG resolution in dots per inch |
| `--cmap` | — | str | `viridis` | Any named matplotlib colormap |
| `--lw` | — | float | auto | Line width in points (auto-scaled if omitted) |
| `--title` | — | str | auto | Custom plot title |
| `--demo` | — | flag | off | Ignore input; render a built-in synthetic signal |

**Level → grid size table:**

| Level | Grid | Cells | Notes |
|-------|------|-------|-------|
| 1 | 2 × 2 | 4 | Trivial; useful only for debugging |
| 4 | 16 × 16 | 256 | Coarse overview |
| 6 | 64 × 64 | 4 096 | **Default** — good balance of detail and speed |
| 8 | 256 × 256 | 65 536 | Fine-grained; requires dense input |
| 10 | 1 024 × 1 024 | 1 048 576 | Maximum; rendering may take several seconds |

Levels above 10 are disallowed because the `LineCollection` for a level-11
curve would contain over 4 million segments, which exceeds practical rendering
limits for a static image.

---

## Examples

### Built-in demo

```bash
python tenet.py --demo
```

Produces `tenet.png` using a synthetic signal composed of sinusoids, a slow
drift, and integrated white noise (a Wiener-like random walk).

### Custom colormap and level

```bash
python tenet.py --demo -l 8 --cmap inferno -o deep_signal
```

Renders the same demo at level 8 (256 × 256 grid) using the `inferno`
colormap, saved as `deep_signal.png`.

### Read from a file

```bash
python tenet.py measurements.csv -l 7 -o result -f pdf
```

### Pipe from another program

```bash
generate_signal.py | python tenet.py - --demo-free -l 6 --cmap coolwarm
```

### Reproduce exactly

```bash
python tenet.py data.txt -l 6 -o figure1 -f pdf --dpi 300 --cmap viridis \
    --title "Sensor A — 24-hour record"
```

---

## Code walkthrough

The source is organised into five functional sections plus the CLI entry point.

---

### Section 1 — Hilbert curve geometry

```python
def _rotate(n, x, y, rx, ry): ...
def d2xy(level, d): ...
def build_hilbert_path(level): ...
```

`_rotate` performs the single-quadrant reflection that is the atomic operation
of Hilbert curve construction.  Given a square of side `n`, current coordinates
`(x, y)`, and the quadrant flags `rx` and `ry`:

* If `ry == 0` and `rx == 1`, the point is reflected across both axes (a 180°
  rotation within the quadrant).
* Regardless of `rx`, if `ry == 0` the axes are then swapped (`x, y = y, x`),
  mirroring the square.

This combination of conditional reflection and transposition is what makes the
curve self-similar: at every level the same rule is applied recursively.

`d2xy` converts a linear Hilbert index `d` to `(x, y)` coordinates.  It works
iteratively rather than recursively: starting from side-length `s = 1` and
doubling on each iteration, it extracts two bits from `d` per step (`rx` from
bit 1, `ry` from bit 0 XOR `rx`), rotates/reflects, then translates by
`s * (rx, ry)`.  After `level` iterations `s` equals `2^level` and `(x, y)` is
the final grid coordinate.  Index `d = 0` maps to `(0, 0)`; index
`d = 4^level − 1` maps to `(0, 1)` (immediately above the origin for even
levels).

`build_hilbert_path` calls `d2xy` for every index `d` in `[0, 4^level)` and
stacks the results into a `(4^level, 2)` NumPy array.  This array is the
ordered sequence of grid vertices through which the curve passes and is used
directly as the source of `LineCollection` segments.

---

### Section 2 — Input/output helpers

```python
def read_input(source): ...
def map_to_curve(col1, col2, n_curve): ...
```

`read_input` accepts either a file path or `'-'` for standard input.  It uses
`numpy.loadtxt` with `comments='#'` so comment lines are silently skipped.
After loading, the data is validated (at least two columns, finite `col1`
values, non-constant `col1`), and rows are sorted by `col1` so that
`numpy.interp` — which requires a monotonically increasing x-axis — behaves
correctly regardless of the order in the source file.

`map_to_curve` bridges the gap between the input's coordinate system and the
integer indices of the Hilbert curve.  It normalises `col1` from its original
range `[min, max]` to `[0, n_curve − 1]`, then calls `numpy.interp` to
evaluate `col2` at every integer position.  The result is a dense array of
length `n_curve` where each element is the signal value assigned to the
corresponding Hilbert cell.  Cells that fall between input samples receive
linearly interpolated values; cells outside the `col1` range (which cannot
occur after normalisation) would be clamped by `numpy.interp`.

---

### Section 3 — Rendering

```python
def plot_hilbert(level, values, *, cmap, lw, title, output, fmt, dpi): ...
```

This function is responsible for the entire visual pipeline:

**Line-width auto-scaling.**  If `--lw` is not supplied, the width is computed
as `max(0.2, 1.6 − 0.18 × level)`.  At level 6 this gives ≈ 0.52 pt; at level
10 it clips to 0.2 pt.  The intent is that the curve fills the canvas at every
level without the segments bleeding into one another.

**Segment construction.**  The `(N, 2)` coordinate array is reshaped to
`(N, 1, 2)` and concatenated with a shifted copy to produce `(N−1, 2, 2)` —
the format expected by `LineCollection`.  Each row of this array is one
directed line segment `[start, end]`.  The colour value assigned to each
segment is the mean of its two endpoint values, producing a smooth colour
gradient along the curve rather than abrupt jumps at each cell boundary.

**LineCollection.**  Using `LineCollection` instead of repeated `ax.plot` calls
is critical for performance: all segments are submitted to the renderer in a
single draw call, and the colour mapping is handled entirely by Matplotlib's
internal machinery.  The collection is added to the axes via `ax.add_collection`
after setting the axis limits manually (because `add_collection` does not
trigger auto-scaling).

**Dark background.**  The figure and axes face-colour are set to `#0d0d0d`
(near-black).  This maximises the perceptual contrast of the default `viridis`
colormap and makes the colour gradient easier to interpret.  The colorbar tick
labels and label are set to white to remain legible.

**Output.**  `plt.savefig` is called with `bbox_inches='tight'` to crop
whitespace, and `facecolor=fig.get_facecolor()` to propagate the dark
background to the saved file.  For PDF output the `dpi` argument is ignored by
Matplotlib (PDFs are vector), but it is accepted without error.

---

### Section 4 — Demo signal generator

```python
def generate_demo(n=4000, seed=42): ...
```

The demo synthesises a signal with three components to exercise the
visualiser's ability to show structure at multiple scales:

1. **Multi-frequency sinusoids** — periods of 200, 47, and 13 units superposed
   with amplitudes 2.5, 1.2, and 0.5 respectively.  These produce visible
   banded regions in the Hilbert plot.
2. **Slow linear drift** — a coefficient of 0.003 × t shifts the baseline
   gradually over the full range, detectable as a systematic colour gradient
   along the curve.
3. **Integrated white noise** — the cumulative sum of standard-normal deviates
   scaled by 0.04 approximates a discrete Wiener process (random walk), adding
   a stochastic component with long-range correlations.

Sampling positions are drawn from a uniform distribution and then sorted, so
the demo also exercises the irregular-sampling path in `read_input`.

---

### Section 5 — CLI (`parse_args` / `main`)

```python
def parse_args(argv=None): ...
def main(argv=None): ...
```

`parse_args` builds the `argparse.ArgumentParser`.  Accepting an explicit
`argv` parameter (defaulting to `None`, which makes `argparse` read
`sys.argv`) allows the parser to be exercised in unit tests without
subprocess overhead.

`main` follows a strict linear pipeline:

1. Parse and validate arguments.  Any `--level` outside [1, 10] triggers an
   error and exits with code 1 before any computation begins.
2. Load or generate data, printing a brief summary to stdout.
3. Build the dense value array by calling `map_to_curve`.
4. Delegate rendering to `plot_hilbert`.

The separation of `parse_args` and `main` from the rendering logic means each
stage can be imported and called independently — useful if `tenet.py` is used
as a library rather than a standalone script.

---

## Performance notes

* **Level 6 (default):** renders in under one second on any modern CPU.
* **Level 8:** `build_hilbert_path` iterates 65 536 times; rendering takes
  roughly 1–3 seconds depending on hardware.
* **Level 10:** 1 048 576 segments; expect 15–60 seconds.  At 300 DPI and
  PNG format the output file will be several megabytes.  Using `--format pdf`
  produces a smaller file but rendering time is similar.
* For exploratory work, use level 6 or 7; reserve level 9–10 for final figures.

---

## Limitations

* **One signal at a time.**  The program maps a single `col2` channel onto the
  curve.  Multi-channel data must be split into separate runs.
* **No temporal axis.**  The Hilbert curve does not have an intrinsic direction
  marker; if the sequence of traversal matters, consider adding start/end
  annotations as a post-processing step.
* **Interpolation artefacts.**  When the input has far fewer rows than curve
  cells (i.e. `len(col1) ≪ 4^level`), large stretches of the curve will be
  linearly interpolated, which may produce misleading gradients.  In this case
  either reduce `--level` or increase the input density.
* **Non-uniform sampling.**  The interpolation is linear in `col1` space, not
  in arc-length along the curve, so signal density is preserved in the `col1`
  dimension but not in the 2-D layout.
