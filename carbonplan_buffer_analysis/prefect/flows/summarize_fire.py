import json

import fsspec
import pandas as pd
import prefect

from carbonplan_buffer_analysis.prefect.flows.calculate_buffer_contributions import (
    get_issuance_table,
)


def get_known_reversals() -> float:
    known_reversals = {
        "trinity": 847_895,
        "eddie_ranch": 276_867,
    }
    return sum(known_reversals.values())


@prefect.task
def load_reversal_summaries():
    fs = fsspec.filesystem("gs")
    fnames = fs.glob("carbonplan-buffer-analysis/outputs/reversals/*")
    store = []
    for fname in fnames:
        with fsspec.open(f"gs://{fname}") as f:
            data = json.load(f)
            store.append(data)
    reversals = pd.DataFrame(store)
    return reversals


@prefect.task
def get_max_loses(issuance: pd.DataFrame) -> dict:
    """sum of allocated arbocs on a per project basis, as of analysis cutoff date"""
    return issuance.groupby("opr_id").allocation.sum().to_dict()


@prefect.task
def summarize_committed_loses(reversals, max_loses):
    reversals.loc[:, "estimated_loss"] = reversals["biomass_loss"] - reversals["salvage_wp"]
    reversals["max_loss"] = reversals["opr_id"].map(max_loses)
    reversals.loc[
        reversals["max_loss"] < reversals["estimated_loss"], "estimated_loss"
    ] = reversals["max_loss"]

    committed_summary = reversals.groupby(
        ["severity", "salvage", "includes_ifm_3"]
    ).estimated_loss.sum()

    return committed_summary


@prefect.task
def summarize_reversals(committed_summary):
    known_reversals = get_known_reversals()
    d = {
        "minimum": committed_summary.min() + known_reversals,
        "maximum": committed_summary.max() + known_reversals,
    }
    with fsspec.open("gs://carbonplan-buffer-analysis/outputs/fire-summary.json", "w") as f:
        json.dump(d, f)


with prefect.Flow("summarize-fire-reversals") as flow:
    issuance = get_issuance_table()
    max_loses = get_max_loses(issuance)
    reversals = load_reversal_summaries()

    committed_summary = summarize_committed_loses(reversals, max_loses)
    summarize_reversals(committed_summary)
