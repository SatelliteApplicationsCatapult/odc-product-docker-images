# Developer's reference for testing Docker images

## TL;DR

Deploy the Redis master service as per below:

```bash
NAMESPACE=odc-routine-products

RELEASEREDIS=redis

helm upgrade --install $RELEASEREDIS stable/redis \
  --namespace $NAMESPACE \
  --version 9.1.3 \
  --values helm/values-redis.yaml
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

Further examples are available under the [../job-examples](../job-examples) folder.

A programmatic job insertion method is discussed [here](https://github.com/SatelliteApplicationsCatapult/ard-docker-images/tree/master/job-insert#using-kubernetes). 

Deploy the worker within the same Kubernetes namespace:

```bash
sed -i "s/namespace:.*/namespace: $NAMESPACE/" deploy.yaml

if [ ! "${RELEASEREDIS}" = "redis" ]; then
  REDIS_SERVICE_HOST=${RELEASEREDIS}-master
  sed -i "s/redis-master/${REDIS_SERVICE_HOST}/g" deploy.yaml
fi

kubectl apply -f deploy.yaml
```

Clean up with:

```bash
helm delete $RELEASEREDIS --purge
kubectl delete -f deploy.yaml
```

### Notes
- DB connection settings for the Open Data Cube are stored in a Kubernetes ConfigMap defined in [deploy.yaml](deploy.yaml)
- the Dask scheduler host is expected to be resolvable as `dask-scheduler.dask.svc.cluster.local`. In case your Dask cluster was deployed in a different Kubernetes namespace, simply amend the value of the `DASK_SCHEDULER_HOST` variable accordingly in [deploy.yaml](deploy.yaml).

## Clean up finished Jobs automatically

A way to clean up finished Jobs (either `Complete` or `Failed`) automatically is to use a [TTL mechanism](https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/#ttl-mechanism-for-finished-jobs).

Note that the TTL mechanism is alpha, with feature gate `TTLAfterFinished`. For more information, see the documentation for [TTL controller for finished resources](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/).

## Enabling the TTL mechanism in Kubernetes

This feature can be enabled with both kube-apiserver and kube-controller-manager feature gate `TTLAfterFinished`.

Using the sudo command, edit the following YAML files:

 - /etc/kubernetes/manifests/kube-apiserver.yaml
 - /etc/kubernetes/manifests/kube-controller-manager.yaml

In each YAML file, add the following statement within the "command" section:

```yaml
- --feature-gates=TTLAfterFinished=true
```

Important: Ensure that you edit the YAML files directly and do not create backup copies of these files in the same directory.

You might have to wait a minute or two for the changes to be detected by Kubernetes.
