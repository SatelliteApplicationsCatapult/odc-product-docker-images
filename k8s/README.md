# Clean up finished Jobs automatically

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
