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


def main():
    with fsspec.open("gs://carbonplan-buffer-analysis/outputs/buffer_contributions.json") as f:
        d = json.load(f)
    natural_risk_buffer = sum([v for k, v in d.items() if not k.startswith("gross")])

    non_natural = d["gross_buffer"] - natural_risk_buffer

    height = 0.45
    fig, ax = plt.subplots()
    fig.set_size_inches(7, 3.5)
    n_bars = 5

    breaks = np.linspace(0, n_bars * height, 5)

    ax.barh(
        breaks[-1],
        d["gross_buffer"],
        height=height,
        color=light["secondary"],
        edgecolor="None",
    )
    ax.barh(
        breaks[-2],
        d["fire_contributions"],
        height=height,
        color=light["red"],
        edgecolor="None",
    )
    ax.barh(
        breaks[-3],
        d["pest_contributions"],
        height=height,
        left=d["fire_contributions"],
        color=light["blue"],
        edgecolor="None",
    )
    ax.barh(
        breaks[-4],
        d["other_contributions"],
        height=height,
        left=d["fire_contributions"] + d["pest_contributions"],
        color=light["orange"],
        edgecolor="None",
    )
    ax.barh(
        breaks[-5],
        d["gross_buffer"] - natural_risk_buffer,
        height=height,
        left=natural_risk_buffer,
        color=light["purple"],
        edgecolor="None",
    )

    ax.annotate(text="Total Buffer Pool", xy=(0, 0.98), xycoords="axes fraction")
    ax.annotate(
        text=f"{d['gross_buffer'] / 1_000_000:.1f}$\,$M ({d['gross_buffer']/ d['gross_buffer'] * 100:.0f}%)",  # noqa
        xy=(0.35, 0.98),
        color=light["secondary"],
        xycoords="axes fraction",
    )

    ax.annotate(text="Wildfire", xy=(0.22, 0.65), xycoords="axes fraction")
    ax.annotate(
        text=f"{d['fire_contributions'] / 1_000_000:.1f}$\,$M ({d['fire_contributions']/ d['gross_buffer'] * 100:.0f}%)",  # noqa
        xy=(0.385, 0.65),
        color=light["red"],
        xycoords="axes fraction",
    )

    ax.annotate(text="Disease & Insect", xy=(0.40, 0.47), xycoords="axes fraction")
    ax.annotate(
        text=f"{d['pest_contributions'] / 1_000_000:.1f}$\,$M ({d['pest_contributions']/ d['gross_buffer'] * 100:.0f}%)",  # noqa
        xy=(0.75, 0.47),
        color=light["blue"],
        xycoords="axes fraction",
    )

    ax.annotate(text="Other", xy=(0.58, 0.29), xycoords="axes fraction")
    ax.annotate(
        text=f"{d['other_contributions'] / 1_000_000:.1f}$\,$M ({d['other_contributions']/ d['gross_buffer'] * 100:.0f}%)",  # noqa
        xy=(0.70, 0.29),
        color=light["orange"],
        xycoords="axes fraction",
    )

    ax.annotate(text="Financial & Management", xy=(0.56, -0.05), xycoords="axes fraction")
    ax.annotate(
        text=f"{ non_natural / 1_000_000:.1f}$\,$M ({non_natural/ d['gross_buffer'] * 100:.0f}%)",  # noqa
        xy=(1.065, -0.05),
        color=light["purple"],
        xycoords="axes fraction",
    )

    plt.ylim(0 - height, breaks[-1] + height)
    plt.xlim(0, d["gross_buffer"])

    plt.axis("off")

    ax.annotate(
        text="Natural\nRisks",
        xy=(-0.2, 0.4),
        xycoords="axes fraction",
        horizontalalignment="center",
    )
    ax.annotate(
        text="Non-natural\nRisks",
        xy=(-0.2, 0),
        xycoords="axes fraction",
        horizontalalignment="center",
    )

    # ax.vlines(x=-10, ymin=0, ymax=1)
    plt.savefig(
        Path(__file__).parents[2] / "img" / "buffer_pool_composition.pdf",
        dpi=300,
        bbox_inches="tight",
    )


if __name__ == "__main__":
    main()
