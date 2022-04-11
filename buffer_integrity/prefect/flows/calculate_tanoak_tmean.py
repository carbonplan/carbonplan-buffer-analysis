import json
from pathlib import Path

import fsspec
import prefect
import xarray


@prefect.task
def load_tmean():

    with fsspec.open(
        "https://carbonplan.blob.core.windows.net/carbonplan-forests/offsets/archive/inputs/prism/conus_tmean.nc"  # noqa
    ) as f:
        ds = xarray.open_dataset(f)

    ds = ds.rename({"__xarray_dataarray_variable__": "tmean"})

    ds = ds.rio.reproject("epsg:4326")
    return ds


@prefect.task
def load_tanoak_basal_area():
    """Load 30m resolution tanoak data, sourced from Lemma"""

    tanoak = xarray.open_rasterio("/home/jovyan/data/rasters/lide3_ba_2017.tif")
    tanoak = tanoak.rio.reproject("epsg:4326")
    return tanoak


@prefect.task
def reproject_tmean(tmean, tanoak):
    #
    tanoak_tmean = tmean.rio.reproject_match(tanoak)
    tanoak_tmean = tanoak_tmean.where(
        tanoak > 0
    )  # casting brings tmean into memory -- use a big machine!
    return tanoak_tmean


@prefect.task
def summarize_tanoak_tmean(tanoak_tmean):
    breaks = [0.25, 0.5, 0.75]
    return {k: v for k, v in zip(breaks, tanoak_tmean["tmean"].quantile(breaks).values)}


@prefect.task
def save_tanoak_tmean(data):
    with open(Path(__file__).parents[3] / "data" / "tanoak-tmean-quantiles.json", "w") as f:
        json.dump(data, f, indent=2)


with prefect.Flow("tanoak-climate-tmean") as flow:
    tmean = load_tmean()
    tanoak = load_tanoak_basal_area()

    tanoak_tmean = reproject_tmean(tmean, tanoak)
    summary = summarize_tanoak_tmean(tanoak_tmean)
    save_tanoak_tmean(summary)
