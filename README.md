# VCS Gitea

## Testing

### CT Tests 
VCS CT tests can be found in /ct-tests

On a physical system, CMS tests can be found in /opt/cray/tests/crayctl-stage{NUMBER}/cms.
Please see https://connect.us.cray.com/confluence/display/DST/Stage+Tests+Guidelines for more details.

example: run CT test for VCS at crayctl stage 4
```
# /opt/cray/tests/crayctl-stage4/cms/vcs_stage4_ct_tests.sh
or
# cmsdev test vcs --ct
```

Tests return 0 for success, 1 otherwise
