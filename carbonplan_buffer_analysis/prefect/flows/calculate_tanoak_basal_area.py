import json

import fsspec
import prefect
from carbonplan_forest_offsets.data import cat


def get_fraction_tanoak(project: dict) -> tuple:
    """Generate project level tanoak summaries"""
    store = []
    if len(project["assessment_areas"]) == 0:
        return 0

    for assessment_area in project["assessment_areas"]:
        tanoak = [x for x in assessment_area["species"] if x["code"] == 631]

        # can be high/low site class -- collapse
        if len(tanoak) > 0:
            tanoak_fraction = sum([x["fraction"] for x in tanoak])
            if assessment_area["code"] == 999:
                acreage = project["acreage"]
            else:
                acreage = assessment_area["acreage"]
            store.append((tanoak_fraction, acreage / project["acreage"]))
        else:
            return 0
    return round(sum([assess_area[0] * assess_area[1] for assess_area in store]), 3)


def load_recent_projects():
    """Manually assembeled tanoak project data

    Manually added projects that have come online after cutoff data
    for original CA forest offsets project.
    """
    return {
        "CAR1313": {"tanoak": 0.17, "ifm-1": 907_671},
        "CAR1329": {"tanoak": 0.024, "ifm-1": 1_831_781},
        "CAR1330": {"tanoak": 0.08, "ifm-1": 840_478},
        "CAR1339": {"tanoak": 0.5159, "ifm-1": 9_754_023},
        "CAR1368": {"tanoak": 0.45, "ifm-1": 1_840_491},
    }


def summarize_project(project):
    fraction = get_fraction_tanoak(project)
    return (
        project["opr_id"],
        {
            "tanoak": fraction,
            "ifm-1": project["rp_1"]["ifm_1"],
        },
    )


def load_ea_projects():
    """Load manually assembled list of early action projects

    Exclusion includes projects that have transitioned from EA, making estimates conservative
    """
    return [
        "CAR657",
        "CAR681",
        "CAR655",
        "CAR696",
        "CAR658",
        "CAR661",
        "CAR660",
        "CAR1004",
        "CAR648",
        "CAR697",
        "CAR408",
        "CAR777",
        "CAR582",
        "CAR645",
        "CAR101",
        "CAR730",
        "CAR780",
        "CAR102",
        "CAR686",
        "CAR1141",  # transitioned,
        "CAR1098",  # transitioned
        "CAR1015",  # EA, didnt transition
        "CAR1100",  # tranistioned
        "CAR1140",  # transitioned
        "CAR1139",  # transitioned
        "CAR429",  # EA, didnt transition (Bascom)
        "CAR1099",  # transitioned
        "CAR1070",  # transitioned
        "CAR1067",  # transitioned
    ]


@prefect.task
def summarize_projects() -> dict:
    retro_json = cat.project_db_json.read()
    summaries = [summarize_project(project) for project in retro_json]

    tanoak_projects = {opr_id: summary for opr_id, summary in summaries if summary["tanoak"] > 0}

    recent_projects = load_recent_projects()

    tanoak_projects.update(recent_projects)
    ea_projects = load_ea_projects()
    tanoak_projects = {k: v for k, v in tanoak_projects.items() if k not in ea_projects}
    return tanoak_projects


@prefect.task
def save_tanoak_projects(tanoak_projects):
    """Write output

    Motivated by difficulties with prefect Results
    """
    with fsspec.open(
        "gs://carbonplan-buffer-analysis/intermediates/tanoak_basal_area.json", "w"
    ) as f:
        json.dump(tanoak_projects, f, indent=2)


with prefect.Flow("tanoak-summaries") as flow:
    tanoak_projects = summarize_projects()
    save_tanoak_projects(tanoak_projects)
