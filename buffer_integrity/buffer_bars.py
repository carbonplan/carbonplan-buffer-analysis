import json
from pathlib import Path

import matplotlib.pyplot as plt
from carbonplan_styles.colors import light
from carbonplan_styles.mpl import set_theme

set_theme(font_scale=1.5)

height = 0.15
top_bar = 0.25
mid_bar = 0.5
bot_bar = 0.75


def plot_base_bars(buffer_data):
    _, ax = plt.subplots(figsize=(7, 3.5))

    ax.barh(top_bar, buffer_data["gross_buffer"], height=height, color=light["secondary"])
    ax.barh(mid_bar, buffer_data["gross_buffer"], height=height, color=light["secondary"])
    ax.barh(bot_bar, buffer_data["gross_buffer"], height=height, color=light["secondary"])
    return ax


def fire_buffer_bars(buffer_data, fire):

    ax = plot_base_bars(buffer_data)

    ax.barh(
        bot_bar,
        buffer_data["fire_contributions"],
        height=height,
        left=buffer_data["gross_buffer"] - buffer_data["fire_contributions"],
        color=light["red"],
    )
    ax.barh(
        mid_bar,
        fire["lower_loss"],
        height=height,
        left=buffer_data["gross_buffer"] - fire["lower_loss"],
        color=light["red"],
    )
    ax.barh(
        top_bar,
        fire["upper_loss"],
        height=height,
        left=buffer_data["gross_buffer"] - fire["upper_loss"],
        color=light["red"],
    )

    ax.barh(
        bot_bar,
        buffer_data["fire_contributions"],
        height=height,
        left=buffer_data["gross_buffer"] - buffer_data["fire_contributions"],
        color=light["red"],
    )
    ax.barh(
        mid_bar,
        fire["lower_loss"],
        height=height,
        left=buffer_data["gross_buffer"] - fire["lower_loss"],
        color=light["red"],
    )
    ax.barh(
        top_bar,
        fire["upper_loss"],
        height=height,
        left=buffer_data["gross_buffer"] - fire["upper_loss"],
        color=light["red"],
    )

    ax.vlines(
        x=buffer_data["gross_buffer"] - buffer_data["fire_contributions"],
        ymin=0,
        ymax=1,
        color=light["primary"],
    )

    ax.annotate(text="Actual:", xy=(0.975, 0.7), xycoords="axes fraction")
    ax.annotate(
        text=f"{buffer_data['fire_contributions'] / 1_000_000:.1f} M",
        xy=(1.1775, 0.7),
        xycoords="axes fraction",
    )

    ax.annotate(text="Upper:", xy=(0.975, 0.23), xycoords="axes fraction")
    ax.annotate(
        text=f"{fire['upper_loss'] / 1_000_000:.1f} M",
        xy=(1.1775, 0.23),
        xycoords="axes fraction",
    )

    ax.annotate(text="Lower:", xy=(0.975, 0.465), xycoords="axes fraction")
    ax.annotate(
        text=f"{fire['lower_loss'] / 1_000_000:.1f} M",
        xy=(1.1775, 0.465),
        xycoords="axes fraction",
    )

    # ax.set_ylim(0,1)
    plt.axis("off")
    plt.savefig(
        Path(__file__).parents[1] / "img" / "fire_buffer_bars.pdf",
        dpi=300,
        bbox_inches="tight",
    )


def insect_buffer_bars(buffer_data, insect):
    ax = plot_base_bars(buffer_data)

    fire_actual = buffer_data["gross_buffer"] - buffer_data["fire_contributions"]

    ax.barh(
        bot_bar,
        buffer_data["fire_contributions"],
        height=height,
        left=fire_actual,
        color=light["red"],
    )
    ax.barh(
        top_bar,
        buffer_data["fire_contributions"],
        height=height,
        left=fire_actual,
        color=light["red"],
    )
    ax.barh(
        mid_bar,
        buffer_data["fire_contributions"],
        height=height,
        left=fire_actual,
        color=light["red"],
    )

    ax.barh(
        bot_bar,
        buffer_data["pest_contributions"],
        height=height,
        left=fire_actual - buffer_data["pest_contributions"],
        color=light["purple"],
    )

    ax.barh(
        top_bar,
        insect["upper_loss"],
        height=height,
        left=fire_actual - insect["upper_loss"],
        color=light["purple"],
    )

    ax.barh(
        mid_bar,
        insect["lower_loss"],
        height=height,
        left=fire_actual - insect["lower_loss"],
        color=light["purple"],
    )

    ax.vlines(
        x=fire_actual - buffer_data["pest_contributions"],
        ymin=0,
        ymax=1,
        color=light["primary"],
    )

    ax.annotate(text="Actual:", xy=(0.975, 0.7), xycoords="axes fraction")
    ax.annotate(
        text=f"{buffer_data['pest_contributions'] / 1_000_000:.1f} M",
        xy=(1.1775, 0.7),
        xycoords="axes fraction",
    )

    ax.annotate(text="Upper:", xy=(0.975, 0.23), xycoords="axes fraction")
    ax.annotate(
        text=f"{insect['upper_loss'] / 1_000_000:.1f} M",
        xy=(1.1775, 0.23),
        xycoords="axes fraction",
    )

    ax.annotate(text="Lower:", xy=(0.975, 0.465), xycoords="axes fraction")
    ax.annotate(
        text=f"{insect['lower_loss'] / 1_000_000:.1f} M",
        xy=(1.1775, 0.465),
        xycoords="axes fraction",
    )

    # ax.set_ylim(0,1)
    plt.axis("off")
    plt.savefig(
        Path(__file__).parents[1] / "img" / "tanoak_buffer_bars.pdf",
        dpi=300,
        bbox_inches="tight",
    )


def main():
    with open(Path(__file__).parents[1] / "data" / "buffer_contributions.json") as f:
        buffer_data = json.load(f)

    mock_fire_data = {"upper_loss": 6_800_000, "lower_loss": 5_800_000}
    mock_bug_data = {"upper_loss": 8_750_000, "lower_loss": 4_750_000}

    fire_buffer_bars(buffer_data, mock_fire_data)
    insect_buffer_bars(buffer_data, mock_bug_data)


if __name__ == "__main__":
    main()
