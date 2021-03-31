# VCS Gitea

This repository contains the Helm Chart for Gitea, packaged as the Version
Control Service (VCS) on Cray Ex (Shasta) systems. It is a part of Cray
System Management (CSM).

### Gitea Version

The version of the community Gitea docker image that is deployed with
this helm chart is found in `kubernetes/gitea/values.yml`:

```yaml
  containers:
    vcs:
      name: vcs
      image:
        repository: cache/gitea
        tag: 1.12.2                # <-- Gitea version
```


## Testing

See cms-tools repo for details on running CT tests for this service.

## License

See `LICENSE`.
