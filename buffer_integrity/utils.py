import json

import fsspec
import geopandas
import pandas as pd


def load_project_geometry(opr_id: str) -> geopandas.GeoDataFrame:
    with fsspec.open(f"gs://carbonplan-forest-offsets/carb-geometries/raw/{opr_id}.json") as f:
        d = json.load(f)

    gdf = geopandas.GeoDataFrame.from_features(d)
    gdf = gdf.set_crs("epsg:4326")
    return gdf


def get_project_centroid(gdf: geopandas.GeoDataFrame) -> tuple:
    """return project centroid in lat/lon space"""
    c = gdf.to_crs("epsg:5070").centroid.to_crs("epsg:4326").item().coords.xy
    return (c[0][0], c[1][0])


def load_sod_blitz() -> geopandas.GeoDataFrame:
    def is_positive(x):
        return x == "positive"

    with fsspec.open("gs://carbonplan-buffer-analysis/inputs/sod-blitz.csv", "r") as f:
        lines = f.readlines()

    obs = [
        (line[1], float(line[-2]), float(line[-3]), is_positive(line[-1]))
        for line in map(lambda x: str(x).strip().split(), lines)
    ]

    df = pd.DataFrame(obs, columns=["id", "lon", "lat", "is_positive"])
    gdf = geopandas.GeoDataFrame(
        df[["id", "is_positive"]],
        geometry=geopandas.points_from_xy(df["lon"], df["lat"]),
    )
    gdf = gdf.set_crs("epsg:4326")
    gdf = gdf[gdf.geometry.is_valid]
    return gdf
