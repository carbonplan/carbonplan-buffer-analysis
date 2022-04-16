import json

import fsspec
import tqdm
from shapely.ops import nearest_points

from carbonplan_buffer_analysis import utils


def get_nearest_point(geometry, points):
    points = nearest_points(geometry, points)
    distance = points[0].distance(points[1])
    return distance


def main():
    with fsspec.open("gs://carbonplan-buffer-analysis/intermediates/tanoak_basal_area.json") as f:
        tanoak_projects = json.load(f)

    sod_blitz = utils.load_sod_blitz()
    positive_sod_blitz = sod_blitz[sod_blitz["is_positive"]].to_crs("epsg:5070").unary_union

    distances = {}

    for opr_id in tqdm.tqdm(tanoak_projects.keys()):
        gdf = utils.load_project_geometry(opr_id).to_crs("epsg:5070")
        geometry = gdf.iloc[0].geometry
        distance = get_nearest_point(geometry, positive_sod_blitz) / 1_000  # km
        distances[opr_id] = distance

    with fsspec.open(
        "gs://carbonplan-buffer-analysis/outputs/distance-to-sod-blitz.json", "w"
    ) as f:
        json.dump(distances, f)


if __name__ == "__main__":
    main()
