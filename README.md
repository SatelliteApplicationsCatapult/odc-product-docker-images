# ODC Product Docker Images
Docker images to routinely create ODC products with Kubernetes.

:warning: A Helm cart to deploy the routine product generation stack is yet to be worked at :warning:

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
VERSION=0.0.52

docker build . -t satapps/odc-products:${VERSION}
docker push satapps/odc-products:${VERSION}
```
