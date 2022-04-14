import json
from pathlib import Path

import fsspec
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from carbonplan_styles.colors import light
from carbonplan_styles.mpl import set_theme

set_theme(font_scale=1.25)
mpl.rc("font", **{"family": "sans-serif", "sans-serif": ["Helvetica"]})

if __name__ == "__main__":
    with fsspec.open("gs://carbonplan-buffer-analysis/outputs/buffer_contributions.json") as f:
        buffer_data = json.load(f)

    with fsspec.open("gs://carbonplan-buffer-analysis/outputs/fire-summary.json") as f:
        estimated_fire_loses = json.load(f)

    height = 0.45
    fig, ax = plt.subplots()
    fig.set_size_inches(7, 3.5)
    n_bars = 5

    breaks = np.linspace(0, n_bars * height, 5)

    ax.barh(
        breaks[-1],
        buffer_data["gross_buffer"],
        height=height,
        color=light["secondary"],
        edgecolor="None",
    )
    ax.barh(
        breaks[-2],
        buffer_data["fire_contributions"],
        height=height,
        color=light["red"],
        edgecolor="None",
    )
    ax.barh(
        breaks[-3],
        estimated_fire_loses["minimum"],
        height=height,
        # left=d["fire_contributions"],
        color=light["red"],
        alpha=0.6,
        edgecolor="None",
    )
    ax.barh(
        breaks[-4],
        estimated_fire_loses["maximum"],
        height=height,
        # left=d["fire_contributions"] + d["pest_contributions"],
        color=light["red"],
        alpha=0.6,
        edgecolor="None",
    )
    ax.barh(
        breaks[-5],
        0,  # d["gross_buffer"] - natural_risk_buffer,
        height=height,
        # left=natural_risk_buffer,
        color="None",
        edgecolor="None",
    )

    ax.annotate(text="", xy=(0, 0.98), xycoords="axes fraction")

    ax.annotate(text="Wildfire", xy=(0.22, 0.65), xycoords="axes fraction")
    ax.annotate(
        text="",
        xy=(0.385, 0.65),
        color=light["red"],
        xycoords="axes fraction",
    )

    min_loss = estimated_fire_loses["minimum"]
    ax.annotate(text="Lower Bound", xy=(0.22, 0.47), xycoords="axes fraction")
    ax.annotate(
        text=f"{ min_loss / 1_000_000:.1f}$\,$M ({min_loss/ buffer_data['fire_contributions'] * 100:.0f}%)",  # noqa
        xy=(0.5, 0.47),
        color=light["secondary"],
        xycoords="axes fraction",
    )

    max_loss = estimated_fire_loses["maximum"]
    ax.annotate(text="Upper Bound", xy=(0.24, 0.29), xycoords="axes fraction")
    ax.annotate(
        text=f"{max_loss / 1_000_000 :.1f}$\,$M ({max_loss/ buffer_data['fire_contributions'] * 100:.0f}%)",  # noqa
        xy=(0.52, 0.29),
        color=light["secondary"],
        xycoords="axes fraction",
    )

    ax.annotate(text="c", alpha=0, xy=(0.565, -0.05), xycoords="axes fraction")
    ax.annotate(
        text="",
        xy=(1.065, -0.05),
        color=light["secondary"],
        xycoords="axes fraction",
    )

    plt.ylim(0 - height, breaks[-1] + height)
    plt.xlim(0, buffer_data["gross_buffer"])

    plt.axis("off")

    ax.vlines(x=buffer_data["fire_contributions"], ymin=0, ymax=2.75, color="k")

    plt.savefig(
        Path(__file__).parents[2] / "img" / "fire-bars.pdf",
        dpi=300,
        bbox_inches="tight",
    )
