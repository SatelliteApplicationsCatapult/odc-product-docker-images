####################
# Geometric median #
####################

import numpy as np
import xarray as xr

import hdstats
import odc.algo
from odc.algo import to_f32, from_float, xr_geomedian

def process_geomedian(dc, client, product, latitude_from, latitude_to, longitude_from, longitude_to, time_from, time_to, output_crs, **kwargs):
    latitude = (float(latitude_from), float(latitude_to))
    longitude = (float(longitude_from), float(longitude_to))
    time_extents = (time_from, time_to)

    data_bands = ['red', 'green', 'blue', 'nir', 'swir1', 'swir2']
    mask_bands = ['pixel_qa' if product.startswith('ls') else 'scene_classification']

    if product.startswith('ls'):
        resolution = (-30, 30)
        group_by='solar_day'
    else:
        resolution = (-10, 10)
        group_by='time'

    xx = dc.load(product=product,
                 time=time_extents,
                 lat=latitude,
                 lon=longitude,
                 output_crs=output_crs,
                 resolution=resolution,
                 #align=(15, 15),
                 measurements=data_bands + mask_bands,
                 group_by=group_by,
                 dask_chunks=dict(
                     x=1000,
                     y=1000)
                )

    if len(xx.time) == 0:
        return None

    scale, offset = (1/10_000, 0)  # differs per product, aim for 0-1 values in float32

    # Identify pixels with valid data (requires working with native resolution datasets)
    if product.startswith('s2'):
        good_quality = (
            (xx.scene_classification == 4) | # mask in VEGETATION
            (xx.scene_classification == 5) | # mask in NOT_VEGETATED
            (xx.scene_classification == 6) | # mask in WATER
            (xx.scene_classification == 7)   # mask in UNCLASSIFIED
        )
    elif product.startswith('ls8'):
        good_quality = (
            (xx.pixel_qa == 322)  | # clear
            (xx.pixel_qa == 386)  |
            (xx.pixel_qa == 834)  |
            (xx.pixel_qa == 898)  |
            (xx.pixel_qa == 1346) |
            (xx.pixel_qa == 324)  | # water
            (xx.pixel_qa == 388)  |
            (xx.pixel_qa == 836)  |
            (xx.pixel_qa == 900)  |
            (xx.pixel_qa == 1348)
        )
    else:
        good_quality = (
            (xx.pixel_qa == 66)   | # clear
            (xx.pixel_qa == 130)  |
            (xx.pixel_qa == 68)   | # water
            (xx.pixel_qa == 132)
        )

    xx_data = xx[data_bands]
    xx_clean = odc.algo.keep_good_only(xx_data, where=good_quality)
    xx_clean = to_f32(xx_clean, scale=scale, offset=offset)
    yy = xr_geomedian(xx_clean,
                      num_threads=1,  # disable internal threading, dask will run several concurrently
                      eps=0.2*scale,  # 1/5 pixel value resolution
                      nocheck=True)   # disable some checks inside geomedian library that use too much ram
    yy = from_float(yy,
                    dtype='int16',
                    nodata=0,
                    scale=1/scale,
                    offset=-offset/scale)

    yy = yy.compute()

    return yy

