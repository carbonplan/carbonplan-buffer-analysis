import json
from pathlib import Path

import fsspec
import pandas as pd
import prefect
from carbonplan_forest_offsets.load.issuance import load_issuance_table

serializer = prefect.engine.serializers.JSONSerializer()
result = prefect.engine.results.LocalResult(
    dir=Path(__file__).parents[3] / "data",
    location="buffer_contributions.json",
    serializer=serializer,
)


@prefect.task
def load_project_fire_risks() -> dict:
    """Load per-project buffer contributions

    Returns:
        dict -- key-value mapping of project OPR ID to buffer contribution
    """
    with fsspec.open("gs://carbonplan-buffer-analysis/project-fire-risks.json") as f:
        d = json.load(f)
    return d


@prefect.task
def get_issuance_table() -> pd.DataFrame:
    """Most recent subset to Q1 compliance instrument report"""
    df = load_issuance_table(most_recent=True, forest_only=False)

    df = df[df["issued_at"] <= pd.Timestamp(2022, 1, 5)].copy()
    return df


@prefect.task
def get_project_issuance(issuance_df: pd.DataFrame) -> dict:
    """Load and subset ARB issuance table

    Returns:
        pd.DataFrame -- subset dataframe that just includes forest projects
    """

    subset = issuance_df[issuance_df["project_type"] == "forest"]

    subset = subset[pd.notna(subset["allocation"])]  # drops verified reversals
    total_issuance = subset.groupby("opr_id")["allocation"].sum().to_dict()
    return total_issuance


@prefect.task
def calculate_fire_buffer(project_issuance: dict, fire_risks: dict) -> float:
    """Calculates the number of ARBOCs placed into the buffer pool for fire related risks

    Arguments:
        project_issuance {dict} -- key-value of OPR-ID to total issuance
        fire_risks {dict} -- key-value of OPR-ID to fire buffer pool contribution

    Returns:
        float -- fire ARBOCs (rounded to two decimal places)
    """
    buffer_contribs = sum(
        [issuance * fire_risks[opr_id] for opr_id, issuance in project_issuance.items()]
    )
    return round(buffer_contribs)


@prefect.task
def calculate_gross_buffer(issuance_df: pd.DataFrame) -> float:
    return round(issuance_df["buffer_pool"].sum())


@prefect.task
def calculate_pest_buffer(project_issuance: dict) -> float:
    return round(sum(project_issuance.values()) * 0.03)  # same for all projects and all protocols!


@prefect.task
def calculate_other_disturb_buffer(project_issuance: dict) -> float:
    return round(sum(project_issuance.values()) * 0.03)  # same for all projects and all protocols!


@prefect.task(result=result)
def summarize_buffer_contributions(
    gross_buffer: float,
    pest_contributions: float,
    other_contributions: float,
    fire_contributions: float,
) -> None:
    """Write json with fire buffer pool number

    Arguments:
        fire_contributions {float} -- Number of buffer pool ARBOCs earmarked for fire
    """

    return {
        "pest_contributions": pest_contributions,
        "fire_contributions": fire_contributions,
        "gross_buffer": gross_buffer,
        "other_contributions": other_contributions,
    }


with prefect.Flow("calculate-fire-buffer") as flow:
    fire_risks = load_project_fire_risks()

    issuance_df = get_issuance_table()
    project_issuance = get_project_issuance(issuance_df)

    gross_buffer = calculate_gross_buffer(issuance_df)
    pest_contributions = calculate_pest_buffer(project_issuance)
    fire_contributions = calculate_fire_buffer(project_issuance, fire_risks)
    other_contributions = calculate_other_disturb_buffer(project_issuance)
    summarize_buffer_contributions(
        gross_buffer, pest_contributions, other_contributions, fire_contributions
    )
