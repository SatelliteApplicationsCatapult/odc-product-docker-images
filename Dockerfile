FROM luigidifraia/dask-datacube:dask-2.14.0-gdal-2.4.4

LABEL maintainer="Luigi Di Fraia"

RUN pip install --quiet --no-cache-dir \
    rio-cogeo==1.1.10

RUN pip install --quiet --no-cache-dir \
    git+https://github.com/SatelliteApplicationsCatapult/datacube-utilities.git#egg=datacube_utilities

COPY scripts/s3.py /s3.py

COPY scripts/export.py /export.py

COPY scripts/masking.py /masking.py

COPY scripts/geomedian.py /geomedian.py

COPY scripts/metadata.py /metadata.py

COPY scripts/utils.py /utils.py

COPY scripts/worker.py /worker.py

COPY scripts/rediswq.py /rediswq.py

CMD [ "python", "worker.py" ]
