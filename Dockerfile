FROM luigidifraia/dask-datacube:v1.1.0-alpha

LABEL maintainer="Luigi Di Fraia"

RUN pip install --quiet \
    Cython \
    hdstats \
    lark-parser \
    odc-algo \
    --extra-index-url=https://packages.dea.ga.gov.au

COPY scripts/s3.py /s3.py

COPY scripts/export.py /export.py

COPY scripts/geomedian.py /geomedian.py

COPY scripts/metadata.py /metadata.py

COPY scripts/worker.py /worker.py

COPY scripts/rediswq.py /rediswq.py

CMD [ "python", "worker.py" ]
