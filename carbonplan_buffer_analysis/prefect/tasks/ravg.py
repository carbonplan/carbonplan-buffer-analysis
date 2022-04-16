import fsspec
import geopandas
import pandas as pd
import prefect
import rioxarray  # noqa
import xarray as xr
from carbonplan_forest_offsets.load.geometry import load_project_geometry

CRS = "+proj=aea +lat_0=23 +lon_0=-96 +lat_1=29.5 +lat_2=45.5 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs"  # noqa
RAVG_RESOLUTION = 30
M2_TO_ACRE = 4046.86
SEVERITY_TO_MORTALITY = {
    1: (0, 0),
    2: (0, 0),  # (0, 0.1),
    3: (0.1, 0.1),  # (0.1, 0.25),
    4: (0.25, 0.25),  # (0.25, 0.5),
    5: (0.5, 0.5),  # (0.5, 0.75),
    6: (0.75, 0.9),
    7: (0.9, 1),
    9: (0, 0),
}


def load_project_nlcd(shp: geopandas.GeoDataFrame) -> xr.DataArray:
    """load nlcd data and clip by shp"""
    nlcd = xr.open_rasterio("gs://carbonplan-buffer-analysis/inputs/nlcd_2013.tif")
    nlcd = nlcd.rio.set_nodata(0)

    bounds = shp.to_crs(nlcd.crs).bounds.to_dict(orient="records")[0]

    subset = nlcd.sel(
        y=slice(bounds["maxy"], bounds["miny"]), x=slice(bounds["minx"], bounds["maxx"])
    )
    subset = subset.rio.set_nodata(0)
    subset = subset.rio.clip(shp.to_crs(CRS).geometry)

    return subset


@prefect.task
def load_ravg(fire_name: str) -> xr.DataArray:
    da = xr.open_rasterio(f"gs://carbonplan-buffer-analysis/inputs/ravg/{fire_name}.tif")
    da = da.rio.set_nodata(0)  # RAVG tifs dont assign nodataval which causes rioxarray to error
    return da


@prefect.task
def get_ravg_subset(ravg: xr.DataArray, opr_id: str) -> xr.DataArray:
    if opr_id == "ACR255":
        # in this case, project may have excluded burned lands
        # load listed shape and mask the ravg data by eligible conifers as opposed to shp file
        with fsspec.open("gs://carbonplan-buffer-analysis/inputs/ACR255-listing.json") as f:
            shp = geopandas.read_file(f)
        ravg_clipped = ravg.rio.clip(shp.to_crs(ravg.crs).geometry)

        listed_nlcd = load_project_nlcd(shp)
        matched = listed_nlcd.rio.reproject_match(ravg_clipped)
        listed_ravg = ravg_clipped.where(matched == 42)
        return listed_ravg.where(listed_ravg > 0)
    else:
        shp = load_project_geometry(opr_id)
        shp = shp.to_crs(ravg.crs)

        # boundary clipping is useful when using CONUS RAVG data
        bounds = shp.bounds.to_dict(orient="records")[0]
        subset = ravg.sel(
            y=slice(bounds["maxy"], bounds["miny"]),
            x=slice(bounds["minx"], bounds["maxx"]),
        )
        subset = subset.rio.set_nodata(0)

        project_pixels = subset.rio.clip(shp.geometry)
        return project_pixels.where(project_pixels > 0)


@prefect.task
def get_ravg_counts(ravg_subset: xr.DataArray) -> dict:
    counts = pd.Series(ravg_subset.where(ravg_subset <= 7).values.ravel()).value_counts().to_dict()
    acre_counts = {k: v * (RAVG_RESOLUTION ** 2) / M2_TO_ACRE for k, v in counts.items()}
    return acre_counts


@prefect.task
def get_mortality_summary(acre_counts: dict) -> dict:

    total_burned = sum(acre_counts.values())

    low = sum(
        [
            SEVERITY_TO_MORTALITY[ba7_class][0] * acre_counts[ba7_class] / total_burned
            for ba7_class in acre_counts.keys()
        ]
    )

    high = sum(
        [
            SEVERITY_TO_MORTALITY[ba7_class][1] * acre_counts[ba7_class] / total_burned
            for ba7_class in acre_counts.keys()
        ]
    )
    return {"low": low, "high": high, "counts": acre_counts}
