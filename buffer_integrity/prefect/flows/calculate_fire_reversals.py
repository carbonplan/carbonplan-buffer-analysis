import json
from itertools import product
from pathlib import Path

import prefect

from buffer_integrity.prefect.tasks import project_reversals


@prefect.task
def load_ravg_summary(fire_name):
    with open(Path(__file__).parents[3] / "data" / f"{fire_name}.json") as f:
        ravg_summary = json.load(f)
    return ravg_summary


with prefect.Flow("project-fire-reversals") as flow:
    severity_level = prefect.Parameter("severity_level")
    salvage_level = prefect.Parameter("salvage_level")
    opr_id = prefect.Parameter("opr_id")
    fire_name = prefect.Parameter("fire_name")
    is_proxy = prefect.Parameter("is_proxy")
    year = prefect.Parameter("year")

    fires = project_reversals.load_fire_perimeters()
    project_fires = project_reversals.get_project_fires(opr_id, fires)

    ravg_summary = load_ravg_summary(fire_name)

    burned_area = project_reversals.calculate_project_burned_area(
        project_fires, ravg_summary, is_proxy, year
    )

    project_reversals.save_project_fires(opr_id, project_fires)

    prefire_biomass = project_reversals.load_prefire_biomass(opr_id)
    storage_factors = project_reversals.load_woodproduct_storage_factors(opr_id)

    biomass_loss = project_reversals.calculate_biomass_loss(
        opr_id, ravg_summary, burned_area, prefire_biomass, severity_level
    )
    salvaged_wp = project_reversals.calculate_salvaged_wood_products(
        biomass_loss, storage_factors, salvage_level
    )

    project_reversals.write_estimate(
        opr_id, biomass_loss, salvaged_wp, severity_level, salvage_level
    )

if __name__ == "__main__":
    severity_levels = ["low", "high"]
    salvage_levels = ["low", "high"]
    events = [
        {"opr_id": "ACR260", "fire_name": "lionshead", "is_proxy": False, "year": 2020},
        {"opr_id": "ACR273", "fire_name": "bootleg", "is_proxy": False, "year": 2021},
        {"opr_id": "ACR255", "fire_name": "north-star", "is_proxy": True, "year": 2021},
        {"opr_id": "CAR1102", "fire_name": "ranch", "is_proxy": True, "year": 2020},
    ]
    for severity_level, salvage_level, event in product(severity_levels, salvage_levels, events):

        flow.run(
            severity_level=severity_level,
            salvage_level=salvage_level,
            **event,
        )
