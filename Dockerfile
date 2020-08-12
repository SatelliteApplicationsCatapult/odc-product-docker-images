FROM satapps/dask-datacube:v3.0.1-alpha

LABEL maintainer="Luigi Di Fraia"

RUN pip install --no-cache-dir \
    rio-cogeo

COPY scripts/ /scripts/

COPY tide-data/ /tide-data/

WORKDIR /scripts/

CMD [ "python", "worker.py" ]
