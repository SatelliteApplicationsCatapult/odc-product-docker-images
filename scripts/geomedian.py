####################
# Geometric median #
####################

import numpy as np
import xarray as xr

import hdstats
import odc.algo
from odc.algo import to_f32, from_float, xr_geomedian
from masking import mask_good_quality

from pyproj import Proj, transform

def process_geomedian(dc, product, query_x_from, query_x_to, query_y_from, query_y_to, time_from, time_to, output_crs, query_crs='EPSG:4326', **kwargs):
    time_extents = (time_from, time_to)

    data_bands = ['red', 'green', 'blue', 'nir', 'swir1', 'swir2']
    mask_bands = ['pixel_qa' if product.startswith('ls') else 'scene_classification']

    if product.startswith('ls'):
        resolution = (-30, 30)
        group_by='solar_day'
        nodata = -9999
    else:
        resolution = (-10, 10)
        group_by='time'
        nodata = 0

    query = {}

    query['product'] = product
    query['time'] = time_extents
    query['output_crs'] = output_crs
    query['resolution'] = resolution
    query['measurements'] = data_bands + mask_bands
    query['group_by'] = group_by
    query['dask_chunks'] = dict(x=1000, y=1000)

    if query_crs != 'EPSG:4326':
        query['crs'] = query_crs

    query['x'] = (float(query_x_from), float(query_x_to))
    query['y'] = (float(query_y_from), float(query_y_to))

    xx = dc.load(**query) # use the query we defined above

    if len(xx.dims) == 0 or len(xx.data_vars) == 0:
        return None

    scale, offset = (1/10_000, 0)  # differs per product, aim for 0-1 values in float32

    # Identify pixels with valid data (requires working with native resolution datasets)
    good_quality = mask_good_quality(xx, product)

    xx_data = xx[data_bands]
    xx_clean = odc.algo.keep_good_only(xx_data, where=good_quality)
    xx_clean = to_f32(xx_clean, scale=scale, offset=offset)
    yy = xr_geomedian(xx_clean,
                      num_threads=1,  # disable internal threading, dask will run several concurrently
                      eps=0.2*scale,  # 1/5 pixel value resolution
                      nocheck=True)   # disable some checks inside geomedian library that use too much ram
    yy = from_float(yy,
                    dtype='int16',
                    nodata=nodata,
                    scale=1/scale,
                    offset=-offset/scale)

    yy = yy.compute()

    return yy

