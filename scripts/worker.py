#!/usr/bin/env python

#################
# Data uploader #
#################

def save_data(ds, job_code, bands, product, time_from, time_to, output_crs, bucket='public-eo-data', prefix='luigi', **kwargs):
    from os.path import basename
    from export import export_xarray_to_geotiff
    from s3 import s3_upload_file

    pn = product[0:3] if product.startswith('ls') else product[0:2]
    no_data = -9999 if product.startswith('ls') else 0

    x_from = float(ds['x'][0])
    x_to = float(ds['x'][-1])
    y_from = float(ds['y'][0])
    y_to = float(ds['y'][-1])

    crs = output_crs.lower().replace(':', '')

    for band in bands:
        destination = f"{prefix}/{pn}_{job_code}_{time_from}_{time_to}_{crs}_{x_from}_{y_from}_{x_to}_{y_to}_{band}.tif"
        fname = basename(destination)

        export_xarray_to_geotiff(ds, fname, bands=[band], no_data=no_data, crs=output_crs, x_coord='x', y_coord='y')

        try:
            s3_upload_file(fname, bucket, destination);

        except Exception as e:
            print("Error: " + str(e))

        finally:
            os.remove(fname)


#####################
# Metadata uploader #
#####################

def save_metadata(ds, job_code, bands, product, time_from, time_to, longitude_from, longitude_to, latitude_from, latitude_to, output_crs, bucket='public-eo-data', prefix='luigi', **kwargs):
    import os
    from os.path import basename
    from metadata import generate_datacube_metadata
    from s3 import s3_upload_file
    import yaml

    pn = product[0:3] if product.startswith('ls') else product[0:2]
    no_data = -9999 if product.startswith('ls') else 0

    x_from = float(ds['x'][0])
    x_to = float(ds['x'][-1])
    y_from = float(ds['y'][0])
    y_to = float(ds['y'][-1])

    crs = output_crs.lower().replace(':', '')

    if product.startswith('ls'):
        satellite = product[2]
        platform = f"LANDSAT_{satellite}"
        if satellite == '4' or satellite == '5':
            instrument = 'TM'
        elif satellite == '7':
            instrument = 'ETM'
        else:
            instrument = 'OLI'
    else:
        platform = 'SENTINEL_2'
        instrument = 'MSI'

    band_base_name = f"{pn}_{job_code}_{time_from}_{time_to}_{crs}_{x_from}_{y_from}_{x_to}_{y_to}"

    destination = f"{prefix}/{pn}_{job_code}_{time_from}_{time_to}_{crs}_{x_from}_{y_from}_{x_to}_{y_to}_datacube-metadata.yaml"
    fname = basename(destination)

    metadata_obj_key = f"s3://{bucket}/{destination}"

    if job_code == 'geomedian':
        doc = generate_datacube_metadata(ds,
                                         bands,
                                         metadata_obj_key,
                                         band_base_name,
                                         'surface_reflectance_statistical_summary',
                                         platform,
                                         instrument,
                                         time_from, time_to,
                                         longitude_from, longitude_to,
                                         latitude_from, latitude_to,
                                         output_crs,
                                         x_from, x_to,
                                         y_from, y_to,
                                         **kwargs)

    if doc:
        with open(fname, 'w') as outfile:
            yaml.dump(doc, outfile)

        try:
            s3_upload_file(fname, bucket, destination);

        except Exception as e:
            print("Error: " + str(e))

        finally:
            os.remove(fname)


###################
# Request handler #
###################

def process_request(dc, client, job_code, **kwargs):
    import gc

    try:
        if job_code == "geomedian":
            from geomedian import process_geomedian

            ds = process_geomedian(dc=dc, client=client, **kwargs)
            save_bands = ['red', 'green', 'blue', 'nir', 'swir1', 'swir2']

        if ds:
            save_data(ds=ds, job_code=job_code, bands=save_bands, **kwargs)
            save_metadata(ds=ds, job_code=job_code, bands=save_bands, **kwargs)

    except Exception as e:
        print("Error: " + str(e))

    finally:
        if ds:
            del ds
            gc.collect()

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
