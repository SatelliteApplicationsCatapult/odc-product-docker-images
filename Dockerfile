FROM luigidifraia/dask-datacube:dask-2.14.0-gdal-2.4.4

LABEL maintainer="Luigi Di Fraia"

RUN pip install --no-cache-dir \
    rio-cogeo==1.1.10

RUN pip install --no-cache-dir \
    git+https://github.com/SatelliteApplicationsCatapult/datacube-utilities.git#egg=datacube_utilities

COPY scripts/ /scripts/

COPY tide-data/ /tide-data/

WORKDIR /scripts/

CMD [ "python", "worker.py" ]
