import json

import fsspec
import pandas as pd
import prefect
import xarray

from carbonplan_buffer_analysis import utils
from carbonplan_buffer_analysis.prefect.flows.calculate_buffer_contributions import (
    get_issuance_table,
)
from carbonplan_buffer_analysis.prefect.flows.calculate_tanoak_tmean import load_tmean

TANOAK_BIOMASS_LOSS = {"minimum": 0.5, "maximum": 0.8}


def load_bay_presence_absence() -> dict:
    """manually assembled k:v of if tanoak projects have California bay laurel
    listed in project documentation
    """
    bay_listed = {
        "ACR262": True,
        "CAR1190": True,
        "CAR1180": True,
        "ACR200": True,
        "ACR182": True,
        "CAR1104": False,
        "CAR1191": True,
        "ACR189": False,
        "CAR1102": True,
        "CAR993": True,
        "ACR378": True,
        "ACR377": True,
        "CAR1174": True,
        "ACR282": True,
        "CAR1103": True,
        "CAR1313": True,
        "CAR1329": True,
        "CAR1330": True,
        "CAR1339": True,
        "CAR1368": False,
    }
    return bay_listed


@prefect.task
def load_tanoak_basal_area():
    with fsspec.open("gs://carbonplan-buffer-analysis/intermediates/tanoak_basal_area.json") as f:
        basal_area = json.load(f)

    return basal_area


@prefect.task
def get_tanoak_biomass(d: dict) -> float:
    """input tanoak records, output total biomass"""
    return {k: v["tanoak"] * v["ifm-1"] for k, v in d.items()}


def get_project_centroid(gdf):
    c = gdf.to_crs("epsg:5070").centroid.to_crs("epsg:4326").item().coords.xy
    return (c[0][0], c[1][0])


@prefect.task
def load_project_tmeans(tanoak_biomass: dict, tmean: xarray.Dataset):
    """get per project tmean data"""
    project_tmean = {}
    for opr_id in tanoak_biomass.keys():
        geom = utils.load_project_geometry(opr_id)
        x, y = get_project_centroid(geom)
        project_tmean[opr_id] = tmean["tmean"].sel(x=x, y=y, method="nearest").values[0]
    return project_tmean


def estimate_biomass_loss(biomass, max_loss):
    return {k: min(max_loss, v * biomass) for k, v in TANOAK_BIOMASS_LOSS.items()}


@prefect.task
def get_max_loses(issuance: pd.DataFrame) -> dict:
    """sum of allocated arbocs on a per project basis, as of analysis cutoff date"""
    return issuance.groupby("opr_id").allocation.sum().to_dict()


@prefect.task
def subset_tmean(tanoak_biomass, project_tmeans):
    median_temp = load_tanoak_median_temp()

    subset = {
        opr_id: biomass
        for opr_id, biomass in tanoak_biomass.items()
        if project_tmeans[opr_id] < median_temp
    }
    return subset


@prefect.task
def subest_bay(tanoak_biomass):
    has_bay = load_bay_presence_absence()
    subset = {opr_id: biomass for opr_id, biomass in tanoak_biomass.items() if has_bay[opr_id]}
    return subset


@prefect.task
def summarize_tanoak_exposure(tanoak_biomass, max_loses):
    def clean_to_write(data: dict):
        return pd.DataFrame(data).sum(axis=1).to_dict()

    loses = {
        opr_id: estimate_biomass_loss(biomass, max_loses[opr_id])
        for opr_id, biomass in tanoak_biomass.items()
    }
    to_write = clean_to_write(loses)
    return to_write


def load_tanoak_median_temp():
    with fsspec.open(
        "gs://carbonplan-buffer-analysis/intermediates/tanoak-tmean-quantiles.json"
    ) as f:
        return json.load(f)["0.5"]


@prefect.task
def summarize_exposure(total_exposure, bay_expsoure, tmean_exposure):
    d = {
        "bay": bay_expsoure,
        "tmean": tmean_exposure,
        "total": total_exposure,
    }
    with fsspec.open("gs://carbonplan-buffer-analysis/outputs/tanoak-summary.json", "w") as f:
        json.dump(d, f)


with prefect.Flow("summarize-tanoak-potential-reversals") as flow:
    issuance = get_issuance_table()
    max_loses = get_max_loses(issuance)

    tanoak_basal_area = load_tanoak_basal_area()
    tanoak_biomass = get_tanoak_biomass(tanoak_basal_area)

    total_exposure = summarize_tanoak_exposure(tanoak_biomass, max_loses)

    bay_subset = subest_bay(tanoak_biomass)
    bay_exposure = summarize_tanoak_exposure(bay_subset, max_loses)

    tmean = load_tmean()
    project_tmeans = load_project_tmeans(tanoak_biomass, tmean)

    tmean_subset = subset_tmean(tanoak_biomass, project_tmeans)
    tmean_exposure = summarize_tanoak_exposure(tmean_subset, max_loses)

    summarize_exposure(total_exposure, bay_exposure, tmean_exposure)
