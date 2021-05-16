# Customizing the deployment 

VCS data claim and postgres database deployment sizes can be configured in the gitea-vcs-init role.

```
---
storage_size_gitea_vcs: 10Gi
storage_size_gitea_db: 10Gi
```

The default sizes are 10Gi for each.