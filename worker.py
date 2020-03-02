#!/usr/bin/env python

###############
# S3 uploader #
###############

def s3_upload_band_file(ds, band, no_data, output_crs, bucket, prefix):
    from os.path import basename
    from export import export_xarray_to_geotiff
    import boto3

    fname = basename(prefix)

    export_xarray_to_geotiff(ds, fname, bands=[band], no_data=no_data, crs=output_crs, x_coord='x', y_coord='y')
    #export_xarray_to_geotiff(ds, fname, bands=[band], no_data=no_data)

    try:
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_s3_endpoint=os.getenv("AWS_S3_ENDPOINT")

        endpoint_url=f"http://{aws_s3_endpoint}"

        s3 = boto3.client('s3',
                          aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          endpoint_url=endpoint_url)

        s3.upload_file(fname, bucket, prefix)

    except Exception as e:
        print("Error: " + str(e))

    finally:
        os.remove(fname)


#################
# Data uploader #
#################

def save_data(ds, type, bands, product, time_from, time_to, output_crs, bucket='public-eo-data', prefix='luigi', **kwargs):
    pn = product[0:3] if product.startswith('ls') else product[0:2]
    no_data = -9999 if product.startswith('ls') else 0

    x_from = float(ds['x'][0])
    x_to = float(ds['x'][-1])
    y_from = float(ds['y'][0])
    y_to = float(ds['y'][-1])

    crs = output_crs.lower().replace(':', '')

    for band in bands:
        s3_upload_band_file(ds,
                            band,
                            no_data,
                            output_crs,
                            bucket,
                            f"{prefix}/{pn}_{type}_{time_from}_{time_to}_{crs}_{x_from}_{y_from}_{x_to}_{y_to}_{band}.tif")


###################
# Request handler #
###################

def process_request(dc, client, type, **kwargs):
    try:
        if type == "geomedian":
            from geomedian import process_geomedian

            ds = process_geomedian(dc=dc, client=client, **kwargs)
            save_bands = ['red', 'green', 'blue', 'nir', 'swir1', 'swir2']

        if ds:
            save_data(ds=ds, type=type, bands=save_bands, **kwargs)

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

