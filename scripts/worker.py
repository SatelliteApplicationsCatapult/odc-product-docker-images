import logging
import os
import rediswq
import signal
from contextlib import contextmanager
from datacube import Datacube
from dask.distributed import Client
from s3 import S3Client
import json
import gc
from utils import save_data, save_metadata, upload_shapefile

###################
# Timeout handler #
###################

@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)

    try:
        yield
    except TimeoutError:
        raise
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)

def raise_timeout(signum, frame):
    raise TimeoutError


###################
# Request handler #
###################

def process_request(dc, s3_client, job_code, **kwargs):
    try:
        if job_code == "geomedian":
            from geomedian import process_geomedian

            ds = process_geomedian(dc=dc, **kwargs)
            save_bands = ['red', 'green', 'blue', 'nir', 'swir1', 'swir2']

        if job_code == "fractional_cover":
            from fractional_cover import process_fractional_cover

            ds = process_fractional_cover(dc=dc, **kwargs)
            save_bands = ['bs', 'pv', 'npv']

        if job_code == "shoreline":
            from shoreline import process_shoreline

            ds, shp_fname = process_shoreline(dc=dc, **kwargs)
            save_bands = ['shoreline']
            upload_shapefile(s3_client=s3_client, ds=ds, fname=shp_fname, job_code=job_code, band='shoreline', **kwargs)

        if ds:
            logging.info("Saving data.")
            save_data(s3_client=s3_client, ds=ds, job_code=job_code, bands=save_bands, **kwargs)
            logging.info("Saving metadata.")
            save_metadata(s3_client=s3_client, ds=ds, job_code=job_code, bands=save_bands, **kwargs)

    except Exception as e:
        logging.error("Unhandled exception %s", e)

    finally:
        if ds:
            del ds
        gc.collect()


#################
# Job processor #
#################

def process_job(dc, dask_client, s3_client, json_data):
    loaded_json = json.loads(json_data)

    try:
        #logging.info("Started processing job."))
        with timeout(timeout_secs):
            process_request(dc, s3_client, **loaded_json)

    except Exception as e:
        logging.error("Unhandled exception %s", e)

    finally:
        dask_client.restart()
        logging.info("Finished processing job.")


##########
# Worker #
##########

def worker():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

    host = os.getenv("REDIS_SERVICE_HOST", "redis-master")
    q = rediswq.RedisWQ(name="jobProduct", host=host)

    logging.info("Worker with sessionID %s.", q.sessionID())
    logging.info("Initial queue state empty=%s.", q.empty())

    host = os.getenv("DASK_SCHEDULER_HOST", "dask-scheduler.dask.svc.cluster.local")
    dask_client = Client(f"{host}:8786")

    dc = Datacube()

    s3_client = S3Client()

    lease_secs = int(os.getenv("JOB_LEASE_PERIOD", "3600"))

    while not q.empty():
        item = q.lease(lease_secs=lease_secs, block=True, timeout=600)
        if item is not None:
            itemstr = item.decode("utf=8")
            logging.info("Working on %s.", itemstr)
            process_job(dc, dask_client, s3_client, itemstr, lease_secs)
            q.complete(item)
        else:
            logging.info("Waiting for work.")

    logging.info("Queue empty, exiting.")

if __name__ == '__main__':
    worker()
