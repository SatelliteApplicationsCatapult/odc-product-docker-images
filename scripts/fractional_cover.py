####################
# Fractional Cover #
####################

import xarray as xr
from datacube_utilities.dc_fractional_coverage_classifier import frac_coverage_classify


def process_fractional_cover(
    dc,
    product,
    query_x_from,
    query_x_to,
    query_y_from,
    query_y_to,
    time_from,
    time_to,
    output_crs,
    query_crs="EPSG:4326",
    dask_time_chunk_size="10",
    dask_x_chunk_size="600",
    dask_y_chunk_size="600",
    **kwargs,
):
    time = (time_from, time_to)

    data_bands = ["red", "green", "blue", "nir", "swir1", "swir2"]

    # Product here is a geomedian product
    if product.startswith("ls"):
        resolution = (-30, 30)
        nodata = -9999
        water_product = product[:3] + "_water_classification"
    else:
        resolution = (-10, 10)
        nodata = 0
        # TODO: Change when S2 WOFS ready
        water_product = None
        return None

    query = {}

    query["output_crs"] = output_crs
    query["resolution"] = resolution
    query["dask_chunks"] = {
        "time": int(dask_time_chunk_size),
        "x": int(dask_x_chunk_size),
        "y": int(dask_y_chunk_size),
    }

    if query_crs != "EPSG:4326":
        query["crs"] = query_crs

    query["x"] = (float(query_x_from), float(query_x_to))
    query["y"] = (float(query_y_from), float(query_y_to))

    water_scenes = dc.load(
        product=water_product, measurements=["water_classification"], time=time, **query
    )
    water_scenes = water_scenes.where(water_scenes >= 0)

    water_composite_mean = water_scenes.water_classification.mean(dim="time")

    land_composite = dc.load(
        product=product, measurements=data_bands, time=time, **query
    )

    if len(land_composite.dims) == 0 or len(land_composite.data_vars) == 0:
        return None

    # Fractional Cover Classification

    frac_classes = xr.map_blocks(
        frac_coverage_classify, land_composite, kwargs={"no_data": nodata}
    )

    # Mask to remove clounds, cloud shadow, and water.
    frac_cov_masked = frac_classes.where(
        (frac_classes != nodata) & (water_composite_mean <= 0.4)
    )

    ## Compute

    fractional_cover = frac_cov_masked.compute()

    return fractional_cover
