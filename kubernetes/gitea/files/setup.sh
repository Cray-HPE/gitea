#!/bin/bash
# Create the admin user for gitea
# Copyright 2019-2021 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)
echo `date` >> /data/gitea/setup
rm -f /data/git/.gitconfig.lock

# Wait for the service to be up and running before attempting to run the cli
echo "Waiting for gitea web service to be available..." >> /data/gitea/setup
attempt_counter=0
max_attempts=30
until $(curl --output /data/gitea/curl --silent --head --fail http://localhost:3000); do
    if [ ${attempt_counter} -eq ${max_attempts} ];then
      echo "Max attempts reached" >> /data/gitea/setup
      exit 1
    fi
    printf '.'
    attempt_counter=$(($attempt_counter+1))
    sleep 5
done

# Wait for secret mounts to be in place before attempting to run the cli
echo "Waiting for vcs user credentials to be available..." >> /data/gitea/setup
attempt_counter=0
max_attempts=30
until $([[ -f "/mnt/crayvcs-credentials/vcs_username" ]]); do
    if [ ${attempt_counter} -eq ${max_attempts} ];then
      echo "Max attempts reached" >> /data/gitea/setup
      exit 1
    fi
    printf '.'
    attempt_counter=$(($attempt_counter+1))
    sleep 5
done

# Setting up crayvcs user, gitea has no way of listing users to check if the
# user already exists, so have to create one and check the return code. Gitea
# issue has been filed: https://github.com/go-gitea/gitea/issues/6001
echo "Creating admin user" >> /data/gitea/setup
CRAYVCS_USER=$(</mnt/crayvcs-credentials/vcs_username)
CRAYVCS_PASSWORD=$(</mnt/crayvcs-credentials/vcs_password)
CRAYVCS_USER_EMAIL="${CRAYVCS_USER}@mgmt-plane-nmn.local"
cd /data/gitea
echo "Running in `pwd`" >> /data/gitea/setup
/app/gitea/gitea admin create-user \
    --config /data/gitea/conf/app.ini \
    --name ${CRAYVCS_USER} \
    --password ${CRAYVCS_PASSWORD} \
    --admin \
    --must-change-password=false \
    --email "${CRAYVCS_USER_EMAIL}" &>> /data/gitea/setup

RESULT=$?
if [ $RESULT == 0 ]; then
  # Leave a breadcrumb that the user has been created
  echo "admin user '${CRAYVCS_USER}' created" >> /data/gitea/setup
  touch /data/gitea/crayvcs_user_created
  echo `date` >> /data/gitea/crayvcs_user_created
else
  echo "User creation failed OR admin user '${CRAYVCS_USER}' has previously been created" >> /data/gitea/setup
fi
