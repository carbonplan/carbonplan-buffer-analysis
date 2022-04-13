import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from carbonplan_styles.colors import light
from carbonplan_styles.mpl import set_theme

set_theme(font_scale=1.25)
mpl.rc("font", **{"family": "sans-serif", "sans-serif": ["Helvetica"]})

if __name__ == "__main__":
    with open(Path(__file__).parents[1] / "data" / "buffer_contributions.json") as f:
        buffer_data = json.load(f)

    with open(Path(__file__).parents[1] / "data" / "fire-summary.json") as f:
        estimated_fire_loses = json.load(f)
    with open(Path(__file__).parents[1] / "data" / "tanoak-summary.json") as f:
        estimated_tanoak_loses = json.load(f)

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
        breaks[-2],
        buffer_data["pest_contributions"],
        height=height,
        color=light["blue"],
        left=buffer_data["fire_contributions"],
        edgecolor="None",
    )

    ax.barh(
        breaks[-3],
        estimated_tanoak_loses["tmean"]["minimum"],
        height=height,
        left=buffer_data["fire_contributions"],
        color=light["blue"],
        alpha=0.6,
        edgecolor="None",
    )
    ax.barh(
        breaks[-4],
        estimated_tanoak_loses["bay"]["minimum"],
        height=height,
        left=buffer_data["fire_contributions"],
        color=light["blue"],
        alpha=0.6,
        edgecolor="None",
    )
    ax.barh(
        breaks[-5],
        estimated_tanoak_loses["total"]["maximum"],
        height=height,
        left=buffer_data["fire_contributions"],
        color=light["blue"],
        alpha=0.6,
        edgecolor="None",
    )

    ax.annotate(text="", xy=(0, 0.98), xycoords="axes fraction")

    ax.annotate(text="Wildfire + Pest & Pathogen", xy=(0.4, 0.65), xycoords="axes fraction")
    ax.annotate(
        text="",
        xy=(0.385, 0.65),
        color=light["red"],
        xycoords="axes fraction",
    )

    million_pad = 0.225
    ax.annotate(text="Scenario A", xy=(0.4, 0.47), xycoords="axes fraction")
    ax.annotate(
        text=f"{estimated_tanoak_loses['tmean']['minimum'] / 1_000_000:.1f}$\,$M ({estimated_tanoak_loses['tmean']['minimum']/ buffer_data['pest_contributions'] * 100:.0f}%)",  # noqa
        xy=(0.4 + 0.225, 0.47),
        color=light["secondary"],
        xycoords="axes fraction",
    )

    ax.annotate(text="Scenario B", xy=(0.42, 0.29), xycoords="axes fraction")
    ax.annotate(
        text=f"{estimated_tanoak_loses['bay']['minimum'] / 1_000_000:.1f}$\,$M ({estimated_tanoak_loses['bay']['minimum']/ buffer_data['pest_contributions'] * 100:.0f}%)",  # noqa
        xy=(0.42 + 0.225, 0.29),
        color=light["secondary"],
        xycoords="axes fraction",
    )

    fourth_bar_y_coord = 0.12

    ax.annotate(text="Scenario C", xy=(0.5, fourth_bar_y_coord), xycoords="axes fraction")
    # ax.annotate(text="Scenario C", xy=(0.57, fourth_bar_y_coord), xycoords="axes fraction")
    ax.annotate(
        text=f"{estimated_tanoak_loses['total']['maximum'] / 1_000_000:.1f}$\,$M ({estimated_tanoak_loses['total']['maximum']/ buffer_data['pest_contributions'] * 100:.0f}%)",  # noqa
        xy=(0.5 + 0.225, fourth_bar_y_coord),
        color=light["secondary"],
        xycoords="axes fraction",
    )
    ax.annotate(
        text="CarbonPlan", alpha=0, xy=(0.22, -0.05), xycoords="axes fraction"
    )  # maintain aspect ratio
    # ax.annotate(text="", xy=(0.57, 0.29), xycoords="axes fraction")

    plt.ylim(0 - height, breaks[-1] + height)
    plt.xlim(0, buffer_data["gross_buffer"])

    plt.axis("off")

    ax.vlines(x=buffer_data["fire_contributions"], ymin=-1, ymax=2.75, color="k")
    ax.vlines(
        x=buffer_data["pest_contributions"] + buffer_data["fire_contributions"],
        ymin=-1,
        ymax=2.75,
        color="k",
    )

    plt.savefig(
        Path(__file__).parents[1] / "img" / "tanoak-bars.pdf",
        dpi=300,
        bbox_inches="tight",
    )
