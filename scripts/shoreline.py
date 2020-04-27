########################
# Shoreline Extraction #
########################

import xarray as xr
import pandas as pd

from datacube_utilities.dea_datahandling import load_ard
import datacube_utilities.waterline_functions_deaafrica as waterline_funcs


def load_tide_data():
    tide_files = "/tide-data/*.csv"
    dfs = []
    # The data here comes from http://www.bom.gov.au/oceanography/projects/spslcmp/data/index.shtml for Fiji
    for f in tide_files:
        # We must read the data now because it doesn't exist on the dask workers
        df = pd.read_csv(f)

        if "Sea Level" in df.columns:
            df["tides"] = df["Sea Level"]
            df = pd.DataFrame.drop(df, columns=["Sea Level"])
        elif "tide" in df.columns:
            df["tides"] = df["tide"]
            df = pd.DataFrame.drop(df, columns=["tide"])
        if " Date & UTC Time" in df.columns:
            df["time"] = df[" Date & UTC Time"]
            df = pd.DataFrame.drop(df, columns=[" Date & UTC Time"])

        dfs.append(df)

    tide_data = pd.concat(dfs)
    tide_data["time"] = pd.to_datetime(tide_data["time"], infer_datetime_format=True)
    tide_data["tide_height"] = tide_data["tides"]
    df = tide_data.set_index("time")
    df = df.loc[~df.index.duplicated(keep="first")]
    df = df[df.tides != -9999]
    df

    return df


def process_shoreline(
    dc,
    query_x_from,
    query_x_to,
    query_y_from,
    query_y_to,
    time_from,
    time_to,
    tide_range_from,
    tide_range_to,
    output_crs,
    query_crs="EPSG:4326",
    dask_time_chunk_size="1",
    dask_x_chunk_size="1500",
    dask_y_chunk_size="1500",
    time_step="1Y",
    **kwargs,
):
    time = (time_from, time_to)

    query = {}

    query["time"] = time
    query["output_crs"] = output_crs
    query["resolution"] = (-30, 30)
    query["dask_chunks"] = {
        "time": int(dask_time_chunk_size),
        "x": int(dask_x_chunk_size),
        "y": int(dask_y_chunk_size),
    }

    if query_crs != "EPSG:4326":
        query["crs"] = query_crs

    query["x"] = (float(query_x_from), float(query_x_to))
    query["y"] = (float(query_y_from), float(query_y_to))

    landsat_ds = load_ard(
        dc=dc,
        products=[
            "ls8_water_classification",
            "ls7_water_classification",
            "ls5_water_classification",
            "ls4_water_classification",
        ],
        group_by="solar_day",
        mask_invalid_data=False,
        mask_pixel_quality=False,
        **query,
    )

    if len(landsat_ds.dims) == 0 or len(landsat_ds.data_vars) == 0:
        return None

    water_classes = landsat_ds.where(landsat_ds >= 0)

    tide_data = load_tide_data()

    # First, we convert the data to an xarray dataset so we can analyse it in the same way as our Landsat data
    tide_data_xr = tide_data.to_xarray()[["tide_height"]].chunk(chunks={"time": -1})

    # We want to convert our hourly tide heights to estimates of exactly how high the tide was at
    # the time that each satellite image was taken. To do this, we can use `.interp` to
    # 'interpolate' a tide height for each Landsat timestamp:
    landsat_tideheights = tide_data_xr.interp(time=water_classes.time)

    # We then want to put these values back into the Landsat dataset so that each image has an estimated tide height:
    water_classes["tide_height"] = landsat_tideheights.tide_height

    # Filter landsat images by tide height
    landsat_hightide = water_classes.where(
        (water_classes.tide_height > tide_range_from)
        & (water_classes.tide_height < tide_range_to),
        drop=True,
    )

    landsat_resampled = landsat_hightide.water.resample(time=time_step).mean("time")

    ## Compute

    landsat_resampled = landsat_resampled.compute()

    shoreline = xr.DataArray.to_dataset(landsat_resampled, dim=None, name="shoreline")

    ## Shapefile

    # Set up attributes to assign to each waterline
    attribute_data = {"time": [str(i)[0:10] for i in landsat_resampled.time.values]}
    attribute_dtypes = {"time": "str"}

    fname = f"output_waterlines.shp"
    waterline_funcs.contour_extract(
        z_values=[0],
        ds_array=landsat_resampled,
        ds_crs=landsat_ds.crs,
        ds_affine=landsat_ds.geobox.transform,
        output_shp=fname,
        attribute_data=attribute_data,
        attribute_dtypes=attribute_dtypes,
        min_vertices=5,
    )

    return shoreline, fname
