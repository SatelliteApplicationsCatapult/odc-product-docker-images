# ODC Product Docker Images

Docker image to routinely generate derived EO products using the [Open Data Cube](https://www.opendatacube.org/) and [Dask](https://dask.org/) within a [Kubernetes](https://kubernetes.io/) platform. YAML metadata for indexing derived products into the Open Data Cube is also created as part of the process.

:warning: A Helm chart to deploy the routine product generation stack (Redis and worker Pods) is yet to be worked at :warning:

## TL;DR

Deploy the Redis master service as per below:

```bash
NAMESPACE=odc-routine-products

RELEASEREDIS=redis

helm upgrade --install $RELEASEREDIS stable/redis \
  --namespace $NAMESPACE \
  --version 9.1.3 \
  --values k8s/helm/values-redis.yaml
```

Add product generation jobs e.g.:

```bash
kubectl run --namespace $NAMESPACE redis-client --rm --tty -i --restart='Never' \
  --image docker.io/bitnami/redis:5.0.5-debian-9-r104 -- bash

cat <<EOF | redis-cli -h redis-master --pipe
rpush jobProduct '{"job_code": "geomedian", "product": "s2_esa_sr_granule", "query_x_from": "2199700.0", "query_y_from": "3549700.0", "query_x_to": "2225300.0", "query_y_to": "3575300.0", "query_crs": "EPSG:3460", "time_from": "2019-01-01", "time_to": "2019-12-31", "output_crs": "EPSG:3460", "prefix": "common_sensing/fiji/sentinel_2_geomedian/2019"}'
rpush jobProduct '{"job_code": "geomedian", "product": "ls8_usgs_sr_scene", "query_x_from": "2099700.0", "query_y_from": "-2400300.0", "query_x_to": "2200300.0", "query_y_to": "-2299700.0", "query_crs": "EPSG:3832", "time_from": "2019-01-01", "time_to": "2019-12-31", "output_crs": "EPSG:3832", "prefix": "common_sensing/vanuatu/landsat_8_geomedian/2019"}'
EOF
exit
```

Further examples are available under the [job-examples](job-examples) folder.

A programmatic job insertion method is discussed [here](https://github.com/SatelliteApplicationsCatapult/ard-docker-images/tree/master/job-insert#using-kubernetes). 

Deploy the worker within the same Kubernetes namespace:

```bash
sed -i "s/namespace:.*/namespace: $NAMESPACE/" k8s/deploy.yaml

if [ ! "${RELEASEREDIS}" = "redis" ]; then
  REDIS_SERVICE_HOST=${RELEASEREDIS}-redis-master
  sed -i "s/redis-master/${REDIS_SERVICE_HOST}/g" k8s/deploy.yaml
fi

kubectl apply -f k8s/deploy.yaml
```

Clean up with:

```bash
helm delete $RELEASEREDIS --purge
kubectl delete -f k8s/deploy.yaml
```

## Notes
- DB connection settings for the Open Data Cube are stored in a Kubernetes ConfigMap defined in [k8s/deploy.yaml](k8s/deploy.yaml)
- the Dask scheduler host is expected to be resolvable as `dask-scheduler.dask.svc.cluster.local`. In case your Dask cluster was deployed in a different Kubernetes namespace, simply amend the value of the `DASK_SCHEDULER_HOST` variable accordingly in [k8s/deploy.yaml](k8s/deploy.yaml).

## Building and pushing to Docker Hub

### Automated builds

Docker images are automatically built and published to [Docker Hub](https://hub.docker.com/u/satapps) from this repo when a release tag, x.y.z, is created.

### Manual builds

Login to docker.io:

```
docker login docker.io
```

Build and upload:

```
VERSION=0.0.89

docker build . -t satapps/odc-products:${VERSION}
docker push satapps/odc-products:${VERSION}
```

## TODO
- Define a Helm chart for templating and value substitution
