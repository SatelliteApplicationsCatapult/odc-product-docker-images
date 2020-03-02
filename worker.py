#!/usr/bin/env python

###################
# Request handler #
###################

def process_request(dc, client, type, product, **kwargs):
    bucket = 'public-eo-data'
    prefix = 'luigi'

    try:
        if type == "geomedian":
            from geomedian import process_geomedian

            ds = process_geomedian(dc=dc, client=client, product=product, **kwargs)

            if ds:
                from export import s3_export_xarray_to_geotiff

                save_bands = ['red', 'green', 'blue', 'nir', 'swir1', 'swir2']
                for band in save_bands:
                    s3_export_xarray_to_geotiff(ds, band, bucket, f"{prefix}/{product}-routine-geomedian-{band}.tif")

    except Exception as e:
        print("Error: " + str(e))

    finally:
        client.restart()

######################
# Product generation #
######################

import json

def process_job(dc, client, json_data):
    loaded_json = json.loads(json_data)
    process_request(dc, client, **loaded_json)

##################
# Job processing #
##################

import rediswq

import os
host = os.getenv("REDIS_SERVICE_HOST", "redis-master")

q = rediswq.RedisWQ(name="jobProduct", host=host)
print("Worker with sessionID: " +  q.sessionID())
print("Initial queue state: empty=" + str(q.empty()))

from datacube import Datacube

dc = Datacube()

import dask
from dask.distributed import Client

client = Client('dask-scheduler.dask.svc.cluster.local:8786')

while not q.empty():
  item = q.lease(lease_secs=1800, block=True, timeout=600) 
  if item is not None:
    itemstr = item.decode("utf=8")
    print("Working on " + itemstr)
    #time.sleep(10) # Put your actual work here instead of sleep.
    process_job(dc, client, itemstr)
    q.complete(item)
  else:
    print("Waiting for work")

print("Queue empty, exiting")

