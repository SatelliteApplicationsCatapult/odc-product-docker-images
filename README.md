# ODC Product Docker Images

Docker image to routinely generate derived EO products using the [Open Data Cube](https://www.opendatacube.org/) and [Dask](https://dask.org/). YAML metadata for indexing derived products into the Open Data Cube is also created as part of the process.

:warning: For operational deployments with [Kubernetes](https://kubernetes.io/), please visit the [Helm Charts repo](https://github.com/SatelliteApplicationsCatapult/helm-charts) instead. :warning:

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
VERSION=0.0.93

docker build . -t satapps/odc-products:${VERSION}
docker push satapps/odc-products:${VERSION}
```
