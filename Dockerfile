FROM satapps/dask-datacube:v1.1.1-alpha

LABEL maintainer="Luigi Di Fraia"

RUN pip install --quiet --no-cache-dir \
    rio-cogeo

COPY scripts/s3.py /s3.py

COPY scripts/export.py /export.py

COPY scripts/geomedian.py /geomedian.py

COPY scripts/metadata.py /metadata.py

COPY scripts/utils.py /utils.py

COPY scripts/worker.py /worker.py

COPY scripts/rediswq.py /rediswq.py

CMD [ "python", "worker.py" ]
