#!/usr/bin/env python

####################
# Geometric median #
####################

def process_request(type):
    import numpy as np
    import xarray as xr

    import hdstats
    import odc.algo
    import dask

    #from dask.distributed import Client
    #client = Client('dask-scheduler.dask.svc.cluster.local:8786')
    #client

    from datacube import Datacube
    from odc.algo import to_f32, from_float, xr_geomedian

    dc = Datacube()

    product = 'ls7_usgs_sr_scene'

    # Sub-region selection - e.g. the city of Suva
    latitude = (-18.2316, -18.0516)
    longitude = (178.2819, 178.6019)

    #time_extents = ('1999-01-01', '2005-01-01')
    time_extents = '2004'

    #dss = dc.find_datasets(product=product,
    #                       time=time_extents,
    #                       lat=latitude,
    #                       lon=longitude)

    mask_bands = ['pixel_qa']

    output_crs = 'EPSG:3460'
    resolution = (-30, 30)

    xx = dc.load(product=product,
                 time=time_extents,
                 lat=latitude,
                 lon=longitude,
                 output_crs=output_crs,
                 resolution=resolution,
                 #align=(15, 15),
                 measurements=data_bands + mask_bands,
                 group_by='solar_day',
                 dask_chunks=dict(
                     x=1000, 
                     y=1000)
                )

    if xx.time == 0:
        return

    scale, offset = (1/10_000, 0)  # differs per product, aim for 0-1 values in float32

    # Identify pixels with valid data (requires working with native resolution datasets)
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

######################
# Product generation #
######################

import json

def process_job(json_data):
    loaded_json = json.loads(json_data)
    process_request(**loaded_json)

##################
# Job processing #
##################

import rediswq

import os
host = os.getenv("REDIS_SERVICE_HOST", "redis-master")

q = rediswq.RedisWQ(name="jobProduct", host=host)
print("Worker with sessionID: " +  q.sessionID())
print("Initial queue state: empty=" + str(q.empty()))

while not q.empty():
  item = q.lease(lease_secs=1800, block=True, timeout=1200) 
  if item is not None:
    itemstr = item.decode("utf=8")
    print("Working on " + itemstr)
    #time.sleep(10) # Put your actual work here instead of sleep.
    process_job(itemstr)
    q.complete(item)
  else:
    print("Waiting for work")

print("Queue empty, exiting")

