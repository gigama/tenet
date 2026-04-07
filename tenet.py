#!/usr/bin/env python3
"""
tenet.py — Stochastic Hilbert Curve Visualizer
=======================================================
Maps a 1-D positional signal onto a 2-D Hilbert space-filling curve.

Input (file or stdin, whitespace/comma-separated, two columns):
    col1  – position along a linear scale, values in [0, MAX]
    col2  – signal value, any real number

The Hilbert curve at LEVEL partitions a 2^LEVEL × 2^LEVEL grid into
4^LEVEL ordered cells.  Each input point is mapped to the nearest cell
via its normalised col1 position; col2 drives the colour map.

Usage examples
--------------
    python tenet.py data.csv
    python tenet.py data.csv -l 8 -o output -f pdf --cmap plasma
    cat data.txt | python tenet.py -         # read from stdin
    python tenet.py --demo                   # built-in demo
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection


# ---------------------------------------------------------------------------
# Hilbert-curve helpers
# ---------------------------------------------------------------------------

def _rotate(n: int, x: int, y: int, rx: int, ry: int):
    """In-place rotation/reflection for one quadrant step."""
    if ry == 0:
        if rx == 1:
            x = n - 1 - x
            y = n - 1 - y
        x, y = y, x
    return x, y


def d2xy(level: int, d: int) -> tuple[int, int]:
    """Convert a 1-D Hilbert index *d* to (x, y) for a 2^level grid."""
    x = y = 0
    s = 1
    while s < (1 << level):
        rx = 1 if (d & 2) else 0
        ry = 1 if (d & 1) ^ rx else 0
        x, y = _rotate(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        d >>= 2
        s <<= 1
    return x, y


def build_hilbert_path(level: int) -> np.ndarray:
    """Return (4^level, 2) float array of ordered (x, y) curve vertices."""
    n_pts = 4 ** level
    return np.array([d2xy(level, d) for d in range(n_pts)], dtype=float)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def read_input(source: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Load two-column data.  *source* is a file path or '-' for stdin.
    Accepts whitespace- or comma-separated files; skips comment lines (#).
    """
    fh = sys.stdin if source == "-" else open(source)
    try:
        data = np.loadtxt(fh, comments="#", delimiter=None)
        if data.ndim == 1:
            data = data.reshape(1, -1)
        if data.shape[1] < 2:
            raise ValueError("Input must contain at least two columns.")
    finally:
        if source != "-":
            fh.close()
    col1, col2 = data[:, 0], data[:, 1]
    if not np.all(np.isfinite(col1)):
        raise ValueError("col1 contains non-finite values.")
    if col1.max() == col1.min():
        raise ValueError("col1 values are all identical — cannot normalise.")
    # Sort by col1 so interpolation is well-defined
    order = np.argsort(col1)
    return col1[order], col2[order]


def map_to_curve(col1: np.ndarray, col2: np.ndarray,
                 n_curve: int) -> np.ndarray:
    """
    Interpolate col2 onto the integer indices [0 … n_curve-1] using col1
    as the independent variable (normalised to that range).

    Returns a float array of length *n_curve*.
    """
    col1_norm = (col1 - col1.min()) / (col1.max() - col1.min()) * (n_curve - 1)
    return np.interp(np.arange(n_curve), col1_norm, col2)


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot_hilbert(
    level: int,
    values: np.ndarray,
    *,
    cmap: str = "viridis",
    lw: float | None = None,
    title: str | None = None,
    output: str = "tenet",
    fmt: str = "png",
    dpi: int = 300,
) -> None:
    """Render the coloured Hilbert curve and save to file."""

    coords = build_hilbert_path(level)
    n_side = 1 << level  # 2^level

    # Auto line-width: thinner at higher levels to avoid bleed
    if lw is None:
        lw = max(0.2, 1.6 - 0.18 * level)

    # Mid-segment colour value for smooth gradients
    seg_vals = (values[:-1] + values[1:]) / 2.0
    vmin, vmax = values.min(), values.max()
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    # Build LineCollection segments: shape (N-1, 2, 2)
    pts = coords[:, np.newaxis, :]          # (N, 1, 2)
    segments = np.concatenate([pts[:-1], pts[1:]], axis=1)

    # Figure — square canvas
    fig_in = min(12.0, 2.0 + 0.8 * n_side ** 0.5)
    fig, ax = plt.subplots(figsize=(fig_in, fig_in))
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_facecolor("#0d0d0d")

    lc = LineCollection(
        segments,
        cmap=cmap,
        norm=norm,
        linewidths=lw,
        capstyle="round",
        joinstyle="round",
        alpha=0.92,
    )
    lc.set_array(seg_vals)
    ax.add_collection(lc)

    ax.set_xlim(-0.7, n_side - 0.3)
    ax.set_ylim(-0.7, n_side - 0.3)

    # Colorbar
    cbar = fig.colorbar(lc, ax=ax, fraction=0.030, pad=0.015,
                        orientation="vertical")
    cbar.set_label("Signal value", color="white", fontsize=9)
    cbar.ax.yaxis.set_tick_params(color="white", labelcolor="white")
    plt.setp(cbar.ax.spines.values(), color="white")

    # Title
    if title is None:
        title = (f"Stochastic Hilbert Curve  "
                 f"[level {level} · {n_side}×{n_side} · {4**level:,} cells]")
    ax.set_title(title, color="white", fontsize=11, pad=8, fontweight="bold")

    outfile = f"{output}.{fmt}"
    plt.savefig(
        outfile, dpi=dpi, format=fmt,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    print(f"Saved → {outfile}  (level={level}, dpi={dpi}, cmap={cmap})")


# ---------------------------------------------------------------------------
# Demo data generator
# ---------------------------------------------------------------------------

def generate_demo(n: int = 4000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """
    Synthesise a stochastic signal: superposition of slow sinusoids,
    pink-ish noise, and a long-range trend.  Returns (col1, col2).
    """
    rng = np.random.default_rng(seed)
    t = np.sort(rng.uniform(0, 1000, n))          # irregular sampling

    # Deterministic component
    signal = (
        2.5 * np.sin(2 * np.pi * t / 200)
        + 1.2 * np.cos(2 * np.pi * t / 47)
        + 0.5 * np.sin(2 * np.pi * t / 13)
        + 0.003 * t                               # slow drift
    )
    # Stochastic component: integrated white noise (Wiener-like)
    wn = rng.standard_normal(n)
    noise = np.cumsum(wn) * 0.04
    return t, signal + noise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "input", nargs="?", default=None,
        help="Two-column data file.  Use '-' for stdin.  "
             "Omit when --demo is set.",
    )
    p.add_argument(
        "-l", "--level", type=int, default=6, metavar="LEVEL",
        help="Hilbert curve level 1–10 (side = 2^LEVEL).  Default: 6.",
    )
    p.add_argument(
        "-o", "--output", default="tenet", metavar="FILENAME",
        help="Output filename without extension.  Default: tenet.",
    )
    p.add_argument(
        "-f", "--format", choices=["pdf", "png"], default="png",
        dest="fmt",
        help="Output format: pdf or png.  Default: png.",
    )
    p.add_argument(
        "--dpi", type=int, default=300,
        help="Resolution in DPI (png only, ignored for pdf).  Default: 300.",
    )
    p.add_argument(
        "--cmap", default="viridis", metavar="COLORMAP",
        help="Matplotlib colormap name.  Default: viridis.",
    )
    p.add_argument(
        "--lw", type=float, default=None, metavar="LINEWIDTH",
        help="Line width in points.  Auto-scaled by level if omitted.",
    )
    p.add_argument(
        "--title", default=None,
        help="Custom plot title.",
    )
    p.add_argument(
        "--demo", action="store_true",
        help="Ignore input file and render a built-in demo signal.",
    )
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # ── Validate level ────────────────────────────────────────────────────
    if not (1 <= args.level <= 10):
        print("Error: level must be between 1 and 10.", file=sys.stderr)
        sys.exit(1)

    # ── Load or generate data ─────────────────────────────────────────────
    if args.demo:
        print("Generating built-in demo signal …")
        col1, col2 = generate_demo()
    elif args.input is None:
        # No file and no --demo: read stdin if it looks like a pipe
        if sys.stdin.isatty():
            print("Error: provide an input file, '-' for stdin, or --demo.",
                  file=sys.stderr)
            sys.exit(1)
        try:
            col1, col2 = read_input("-")
        except Exception as exc:
            print(f"Error reading stdin: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        src = args.input
        if src != "-" and not Path(src).is_file():
            print(f"Error: file not found — {src}", file=sys.stderr)
            sys.exit(1)
        try:
            col1, col2 = read_input(src)
        except Exception as exc:
            print(f"Error reading {src!r}: {exc}", file=sys.stderr)
            sys.exit(1)

    print(f"Points loaded : {len(col1):,}")
    print(f"col1 range    : [{col1.min():.4g}, {col1.max():.4g}]")
    print(f"col2 range    : [{col2.min():.4g}, {col2.max():.4g}]")

    # ── Map signal onto Hilbert indices ───────────────────────────────────
    n_curve = 4 ** args.level
    print(f"Curve cells   : {n_curve:,}  ({1 << args.level}×{1 << args.level} grid)")
    values = map_to_curve(col1, col2, n_curve)

    # ── Render ────────────────────────────────────────────────────────────
    plot_hilbert(
        args.level,
        values,
        cmap=args.cmap,
        lw=args.lw,
        title=args.title,
        output=args.output,
        fmt=args.fmt,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
