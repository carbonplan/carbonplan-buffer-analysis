import datetime
import json

import fsspec
import geopandas
import numpy as np
import pandas as pd
import prefect
from carbonplan_forest_offsets.load.geometry import load_project_geometry
from carbonplan_forest_offsets.load.project_db import load_project_data

CRS = "+proj=aea +lat_0=23 +lon_0=-96 +lat_1=29.5 +lat_2=45.5 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs"  # noqa
M2_TO_ACRE = 4046.86
SALVAGE_FRACTIONS = {"low": 0.1, "mid": 0.2, "high": 0.3}


def load_nifc_fires():
    """load nifc data for 2020/2021 fire season

    NB this is a bit of an undocumented NIFC feature -- the data supposedly only cover 2021
    but there are definitely 2020 fires included at the endpoint.
    This might not be true in the future.

    https://data-nifc.opendata.arcgis.com/datasets/
    nifc::wfigs-wildland-fire-perimeters-full-history/about
    """
    with fsspec.open(
        'gs://carbonplan-buffer-analysis/inputs/nifc_perimeters_2020_2021.geojson'
    ) as f:
        fires = geopandas.read_file(f)

    nifc_colnames = {"poly_IncidentName": "name", "poly_Acres_AutoCalc": "acres"}
    fires = fires.rename(columns=nifc_colnames)

    fires = fires[fires["irwin_FireDiscoveryDateTime"].str[:4].isin(["2020", "2021"])]

    fires["ignite_at"] = (
        fires["irwin_FireDiscoveryDateTime"]
        .apply(pd.Timestamp)
        .apply(lambda x: pd.Timestamp(x.date()))
    )

    return fires.to_crs(CRS)[["name", "acres", "ignite_at", "geometry"]]


def load_mtbs_fires():
    """
    load mtbs data

    Originally from: https://www.mtbs.gov/direct-download
    """
    with fsspec.open("gs://carbonplan-buffer-analysis/inputs/mtbs_perimeters_2019.json") as f:
        fires = geopandas.read_file(f)

    fires = fires[fires["Incid_Type"] == "Wildfire"]

    mtbs_colnames = {"Incid_Name": "name", "BurnBndAc": "acres"}
    fires = fires.rename(columns=mtbs_colnames)

    fires["ignite_at"] = fires["Ig_Date"].apply(pd.Timestamp)

    return fires.to_crs(CRS)[["name", "acres", "ignite_at", "geometry"]]


def load_fires():
    print("loading nifc data")
    nifc = load_nifc_fires()
    print("loading mtbs data")
    mtbs = load_mtbs_fires()
    return pd.concat([nifc, mtbs])


@prefect.task(cache_for=datetime.timedelta(hours=1))
def load_fire_perimeters() -> geopandas.GeoDataFrame:
    """Load MTBS and NIFC fire perimeteres

    Returns:
        geopandas.GeoDataFrame -- shapes and ignition dates
    """
    return load_fires()


@prefect.task
def load_prefire_biomass(opr_id: str) -> dict:
    """Load onsite biomass before fire event,

    Arguments:
        opr_id {str} -- project id

    Returns:
        dict -- carbon stocks broken down by various pools (i.e., ifm-1 - standing live)
    """
    with fsspec.open(
        "gs://carbonplan-buffer-analysis/inputs/adjusted_prefire_carbon_stocks.json",
        "r",
    ) as f:
        d = json.load(f)
        return d[opr_id.lower()]


@prefect.task
def load_woodproduct_storage_factors(opr_id: str) -> dict:
    with fsspec.open(
        "gs://carbonplan-buffer-analysis/inputs/wood_product_storage_factors.json",
        "r",
    ) as f:
        d = json.load(f)
        return d[opr_id.lower()]


@prefect.task
def get_project_fires(opr_id: str, fires: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
    """intersection of project geometry and MTBS/NIFC fires"""
    geom = load_project_geometry(opr_id)
    if not np.all(geom.is_valid):
        geom.geometry = geom.buffer(0)

    project_data = load_project_data(opr_id)
    start_dt = datetime.datetime.strptime(project_data["rp_1"]["start_date"], "%Y-%m-%d")

    eligible_fires = fires[(fires["ignite_at"] > start_dt)].copy()
    project_fires = geopandas.sjoin(eligible_fires, geom.to_crs(fires.crs))
    intersect_fires = geopandas.clip(project_fires, geom.to_crs(fires.crs))

    intersect_fires["acres"] = intersect_fires.area / M2_TO_ACRE

    return intersect_fires


@prefect.task
def save_project_fires(opr_id: str, project_fires: geopandas.GeoDataFrame) -> None:
    """Save project fires to /tmp as part of debug/analysis"""
    to_save = project_fires.copy()  # below modifies global object, make a copy.

    to_save["ignite_at"] = to_save["ignite_at"].astype(
        str
    )  # cannot get geopandas.to_json to serialize datetimes

    with fsspec.open(f"/tmp/{opr_id}_fires.geojson", "wb") as f:
        to_save.to_crs("epsg:4326").to_file(f, driver="GeoJSON")


@prefect.task
def calculate_project_burned_area(
    project_fires: geopandas.GeoDataFrame, ravg_summary: dict, is_proxy: bool, year: int
) -> float:
    # proxy area comes from fire perims, otherwise from RAVG
    if is_proxy:
        reversal_year_fires = project_fires[project_fires["ignite_at"].dt.year == year]
        fire_area = reversal_year_fires.unary_union.area  # remove overlaps
        return fire_area / M2_TO_ACRE
    else:
        return sum(ravg_summary["counts"].values())


@prefect.task
def calculate_biomass_loss(
    opr_id: str,
    ravg_data: dict,
    burned_area: float,
    prefire_biomass: dict,
    severity_level: str,
    include_ifm3: bool = False,
) -> float:
    """Calculates tons of CO2 lost from specific fire event

    Arguments:
        opr_id {str} -- project id
        ravg_data {dict} -- acres by severity class summary of ravg fire event
        burned_area {Union[float, None]} -- Number of acres burned. If None, take from ravg_data
        prefire_biomass {dict} -- Tons of CO2 at risk
        severity_level {str} -- ravg_data estimates has low and high estiamtes of mortality
        include_ifm3 {bool} -- include CWD (ifm3) in loss estimates
    Returns:
        float -- number of tons burned
    """

    if include_ifm3:
        onsite_carbon = (
            prefire_biomass["ifm-1"] + prefire_biomass["ifm-3"]
        )  # too conservative? loses include ifm-3
    else:
        onsite_carbon = prefire_biomass["ifm-1"]

    project_area = load_project_data(opr_id)["acreage"]

    frac_burned = burned_area / project_area

    weighted_loss = ravg_data[severity_level]
    return onsite_carbon * frac_burned * weighted_loss


@prefect.task
def calculate_salvaged_wood_products(
    biomass_loss: float, storage_factors: dict, salvage_level: str
) -> float:
    """Calculate tCO2 locked up in wood proucts

    If ifm-3 included in loss, allow salvage.

    Arguments:
        biomass_loss {float} -- total biomass lost in fire
        storage_factors {dict} -- project-specific storage factors for landfill and in-use products
        salvage_level {str} -- fraction of lost biomass that is salavges [low, mid, high]

    Returns:
        float -- tCO2 stored in wood products
    """
    salvage_fraction = SALVAGE_FRACTIONS.get(salvage_level)
    frac_merch = storage_factors["frac_merch"]
    if salvage_level != "low":
        frac_merch = 0.645  # if not low, assume max observed across 4 projects
    return (
        biomass_loss  # noqa
        * salvage_fraction  # noqa
        * frac_merch  # noqa
        * (storage_factors["lf_frac"] + storage_factors["inuse_frac"])  # noqa
    )  # noqa


@prefect.task
def write_estimate(
    opr_id: str,
    biomass_loss: float,
    salvaged_wp: float,
    severity_level: str,
    salvage_level: str,
    ifm_3: bool,
) -> None:
    fn = f"gs://carbonplan-buffer-analysis/outputs/reversals/{opr_id}_severity-{severity_level}_salvage-{salvage_level}_ifm3-{str(ifm_3).lower()}.json"  # noqa

    record = {
        "opr_id": opr_id,
        "biomass_loss": biomass_loss,
        "salvage_wp": salvaged_wp,
        "severity": severity_level,
        "salvage": salvage_level,
        "includes_ifm_3": str(ifm_3).lower(),
    }
    with fsspec.open(fn, "w") as f:
        json.dump(record, f, indent=2)
