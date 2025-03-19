import json

import fsspec
import prefect
import rioxarray  # noqa
import xarray


@prefect.task
def load_tmean():

    with fsspec.open(
        "https://carbonplan-forests.s3.us-west-2.amazonaws.com/offsets/archive/inputs/prism/conus_tmean.nc"  # noqa
    ) as f:
        ds = xarray.open_dataset(f)

    ds = ds.rename({"__xarray_dataarray_variable__": "tmean"})

    ds = ds.rio.reproject("epsg:4326")
    return ds


@prefect.task
def load_tanoak_lemma():
    """Load 30m resolution tanoak data, sourced from Lemma"""
    tanoak = xarray.open_rasterio("gs://carbonplan-buffer-analysis/inputs/lide3_ba_2017.tif")
    tanoak = tanoak.rio.reproject("epsg:4326")
    return tanoak


@prefect.task
def reproject_tmean(tmean, tanoak):
    """Align tmean and tanoak biomass data

    This doesn't currently use chunking and requires a big machine
    """
    tanoak_tmean = tmean.rio.reproject_match(tanoak)
    tanoak_tmean = tanoak_tmean.where(
        tanoak > 0
    )  # casting brings tmean into memory -- use a big machine!
    return tanoak_tmean


@prefect.task
def summarize_tanoak_tmean(tanoak_tmean):
    """calculate IQR and median tmean across tanoak range"""
    breaks = [0.25, 0.5, 0.75]
    return {k: v for k, v in zip(breaks, tanoak_tmean["tmean"].quantile(breaks).values)}


@prefect.task
def save_tanoak_tmean(data):
    with fsspec.open(
        "gs://carbonplan-buffer-analysis/intermediates/tanoak-tmean-quantiles.json", "w"
    ) as f:
        json.dump(data, f, indent=2)


with prefect.Flow("tanoak-climate-tmean") as flow:
    tmean = load_tmean()
    tanoak = load_tanoak_lemma()

    tanoak_tmean = reproject_tmean(tmean, tanoak)
    summary = summarize_tanoak_tmean(tanoak_tmean)
    save_tanoak_tmean(summary)
