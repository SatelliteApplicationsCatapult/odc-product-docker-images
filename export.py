import os
from os.path import basename

import boto3
import xarray as xr
import rasterio

def _get_transform_from_xr(data, x_coord='longitude', y_coord='latitude'):
    """Create a geotransform from an xarray.Dataset or xarray.DataArray.
    """

    from rasterio.transform import from_bounds
    geotransform = from_bounds(data[x_coord][0], data[y_coord][-1],
                               data[x_coord][-1], data[y_coord][0],
                               len(data[x_coord]), len(data[y_coord]))
    return geotransform


def export_xarray_to_geotiff(data, tif_path, bands=None, no_data=-9999, crs="EPSG:4326",
                             x_coord='longitude', y_coord='latitude'):
    """
    Export a GeoTIFF from a 2D `xarray.Dataset`.
    Parameters
    ----------
    data: xarray.Dataset or xarray.DataArray
        An xarray with 2 dimensions to be exported as a GeoTIFF.
    tif_path: string
        The path to write the GeoTIFF file to. You should include the file extension.
    bands: list of string
        The bands to write - in the order they should be written.
        Ignored if `data` is an `xarray.DataArray`.
    no_data: int
        The nodata value.
    crs: string
        The CRS of the output.
    x_coord, y_coord: string
        The string names of the x and y dimensions.
    """
    if isinstance(data, xr.DataArray):
        height, width = data.sizes[y_coord], data.sizes[x_coord]
        count, dtype = 1, data.dtype
    else:
        if bands is None:
            bands = list(data.data_vars.keys())
        else:
            assrt_msg_begin = "The `data` parameter is an `xarray.Dataset`. "
            assert isinstance(bands, list), assrt_msg_begin + "Bands must be a list of strings."
            assert len(bands) > 0 and isinstance(bands[0], str), assrt_msg_begin + "You must supply at least one band."
        height, width = data.dims[y_coord], data.dims[x_coord]
        count, dtype = len(bands), data[bands[0]].dtype
    with rasterio.open(
            tif_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=count,
            dtype=dtype,
            crs=crs,
            transform=_get_transform_from_xr(data, x_coord=x_coord, y_coord=y_coord),
            nodata=no_data) as dst:
        if isinstance(data, xr.DataArray):
            dst.write(data.values, 1)
        else:
            for index, band in enumerate(bands):
                dst.write(data[band].values.astype(dtype), index + 1)
    dst.close()


def s3_export_xarray_to_geotiff(ds, band, bucket, prefix, **kwargs):
    fname = basename(prefix)

    #export_xarray_to_geotiff(ds, fname, bands=[band], crs="EPSG:3460", x_coord='x', y_coord='y')
    export_xarray_to_geotiff(ds, fname, bands=[band])

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

