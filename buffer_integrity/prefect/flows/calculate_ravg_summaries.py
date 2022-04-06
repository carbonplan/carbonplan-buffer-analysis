import json
from pathlib import Path

import prefect

from buffer_integrity.prefect.tasks import ravg


@prefect.task
def save_ravg_summary(fire_name, ravg_summary):
    # print(Path(__file__))
    with open(Path(__file__).parents[3] / "data" / f"{fire_name}.json", "w") as f:
        json.dump(ravg_summary, f)


with prefect.Flow("summarize-ravg") as flow:

    fire_name = prefect.Parameter("fire_name")
    opr_id = prefect.Parameter("opr_id")

    ravg_data = ravg.load_ravg(fire_name)
    subset_ravg = ravg.get_ravg_subset(ravg_data, opr_id)
    counts = ravg.get_ravg_counts(subset_ravg)
    ravg_summary = ravg.get_mortality_summary(counts)
    save_ravg_summary(fire_name, ravg_summary)

if __name__ == "__main__":
    for params in [
        {"opr_id": "ACR255", "fire_name": "north-star"},
        {"opr_id": "CAR1174", "fire_name": "ranch"},
        {"opr_id": "ACR260", "fire_name": "lionshead"},
        {"opr_id": "ACR273", "fire_name": "bootleg"},
    ]:
        flow.run(**params)
