import logging
import os
from os.path import basename
from export import export_xarray_to_geotiff
from metadata import generate_datacube_metadata
import yaml

#########
# Utils #
#########

def get_ds_extents(ds):
    x_from = float(ds['x'][0])
    x_to = float(ds['x'][-1])
    y_from = float(ds['y'][0])
    y_to = float(ds['y'][-1])

    return x_from, x_to, y_from, y_to


#################
# Data uploader #
#################

def save_data(s3_client,
              ds,
              job_code,
              bands,
              product,
              time_from, time_to,
              output_crs,
              bucket='public-eo-data', prefix='luigi',
              wgs84_naming='True',
              cogeo_output='True',
              **kwargs):
    """
    Save raster data for each band in the list of bands
    """

    pn = product[0:3] if product.startswith('ls') else product[0:2]
    no_data = -9999 if product.startswith('ls') else 0

    if wgs84_naming == 'True':
        x_from = kwargs.get('longitude_from')
        x_to = kwargs.get('longitude_to')
        y_from = kwargs.get('latitude_from')
        y_to = kwargs.get('latitude_to')
    else:
        x_from, x_to, y_from, y_to = get_ds_extents(ds)

    crs = output_crs.lower().replace(':', '')

    for band in bands:
        destination = f"{prefix}/{pn}_{job_code}_{time_from}_{time_to}_{crs}_{x_from}_{y_from}_{x_to}_{y_to}_{band}.tif"

        fname = basename(destination)
        logging.debug("Saving band file %s.", fname)

        if output_crs == 'EPSG:4326':
            export_xarray_to_geotiff(ds, fname, bands=[band], no_data=no_data)
        else:
            export_xarray_to_geotiff(ds, fname, bands=[band], no_data=no_data, crs=output_crs, x_coord='x', y_coord='y')

        if cogeo_output == 'True':
            import shlex, subprocess

            # TODO: use the Python API directly, albeit memory cleanup might be more effective using subprocess?
            args = shlex.split(f"rio cogeo create {fname} {fname} --co PREDICTOR=2 --co ZLEVEL=9 --cog-profile deflate --overview-level 5 --overview-resampling average")

            # DONT: don't capture the output from rio cogeo as it is already part of this process's stdout/stderr so it's available in Kubernetes' logs
            cog_status = subprocess.call(args)

            if cog_status:
               logging.error("COG conversion failed for file %s.", fname)

        try:
            s3_client.upload_file(fname, bucket, destination);

        except Exception as e:
            logging.error("Unhandled exception %s", e)

        finally:
            os.remove(fname)


#####################
# Metadata uploader #
#####################

def save_metadata(s3_client,
                  ds,
                  job_code,
                  bands,
                  product,
                  time_from, time_to,
                  longitude_from, longitude_to,
                  latitude_from, latitude_to,
                  output_crs,
                  bucket='public-eo-data', prefix='luigi',
                  wgs84_naming=True,
                  **kwargs):
    """
    Save YAML manifest for each band in the list of bands
    """

    pn = product[0:3] if product.startswith('ls') else product[0:2]

    if wgs84_naming == True:
        x_from = longitude_from
        x_to = longitude_to
        y_from = latitude_from
        y_to = latitude_to
    else:
        x_from, x_to, y_from, y_to = get_ds_extents(ds)

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
    logging.debug("Saving metadata file %s.", fname)

    metadata_obj_key = f"s3://{bucket}/{destination}"

    x_from, x_to, y_from, y_to = get_ds_extents(ds)

    if job_code == 'geomedian':
        doc = generate_datacube_metadata(metadata_obj_key,
                                         bands,
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
            s3_client.upload_file(fname, bucket, destination);

        except Exception as e:
            logging.error("Unhandled exception %s", e)

        finally:
            os.remove(fname)

