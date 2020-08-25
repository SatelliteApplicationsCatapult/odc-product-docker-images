FROM satapps/dask-datacube:v3.1.0-alpha

LABEL maintainer="Luigi Di Fraia"

RUN pip install --no-cache-dir \
    rio-cogeo

COPY scripts/ /scripts/

COPY tide-data/ /tide-data/

WORKDIR /scripts/

CMD [ "python", "worker.py" ]
