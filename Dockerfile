FROM satapps/dask-datacube:v2.1.0-alpha

LABEL maintainer="Luigi Di Fraia"

RUN pip install --no-cache-dir \
    rio-cogeo==1.1.10

COPY scripts/ /scripts/

COPY tide-data/ /tide-data/

WORKDIR /scripts/

CMD [ "python", "worker.py" ]
