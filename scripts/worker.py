import logging
from utils import save_data, save_metadata

###################
# Request handler #
###################

def process_request(dc, client, s3_client, job_code, **kwargs):
    import gc

    try:
        if job_code == "geomedian":
            from geomedian import process_geomedian

            ds = process_geomedian(dc=dc, client=client, **kwargs)
            save_bands = ['red', 'green', 'blue', 'nir', 'swir1', 'swir2']

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
        client.restart()


#################
# Job processor #
#################

def process_job(dc, client, s3_client, json_data):
    import json
    from datetime import datetime

    loaded_json = json.loads(json_data)

    try:
        #logging.info("Started processing job."))
        process_request(dc, client, s3_client, **loaded_json)

    except Exception as e:
        logging.error("Unhandled exception %s", e)

    finally:
        logging.info("Finished processing job.")


##########
# Worker #
##########

def worker():
    import os
    import rediswq
    from datacube import Datacube
    from dask.distributed import Client
    from s3 import S3Client

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

    host = os.getenv("REDIS_SERVICE_HOST", "redis-master")
    q = rediswq.RedisWQ(name="jobProduct", host=host)
    logging.info("Worker with sessionID %s.", q.sessionID())
    logging.info("Initial queue state empty=%s.", q.empty())

    host = os.getenv("DASK_SCHEDULER_HOST", "dask-scheduler.dask.svc.cluster.local")
    client = Client(f"{host}:8786")

    dc = Datacube()

    s3_client = S3Client()

    while not q.empty():
      item = q.lease(lease_secs=1800, block=True, timeout=600)
      if item is not None:
        itemstr = item.decode("utf=8")
        logging.info("Working on %s.", itemstr)
        process_job(dc, client, s3_client, itemstr)
        q.complete(item)
      else:
        logging.info("Waiting for work.")

    logging.info("Queue empty, exiting.")

if __name__ == '__main__':
    worker()
