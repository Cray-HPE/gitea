#!/bin/bash
#
# MIT License
#
# (C) Copyright 2019-2022 Hewlett Packard Enterprise Development LP
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# Create the admin user for gitea

DATA_MOUNT=/var/lib/gitea
LOG_FILE=${DATA_MOUNT}/setup.log
echo `date` >> $LOG_FILE
rm -f ${DATA_MOUNT}/git/.gitconfig.lock

# Wait for the service to be up and running before attempting to run the cli
echo "Waiting for gitea web service to be available..." >> $LOG_FILE
attempt_counter=0
max_attempts=30
until $(curl --output ${DATA_MOUNT}/curl.out --silent --fail http://localhost:3000); do
    if [ ${attempt_counter} -eq ${max_attempts} ];then
      echo "Max attempts reached" >> $LOG_FILE
      exit 1
    fi
    printf '.'
    attempt_counter=$(($attempt_counter+1))
    sleep 5
done

# Wait for secret mounts to be in place before attempting to run the cli
echo "Waiting for vcs user credentials to be available..." >> $LOG_FILE
attempt_counter=0
max_attempts=30
until $([[ -f "/mnt/crayvcs-credentials/vcs_username" ]]); do
    if [ ${attempt_counter} -eq ${max_attempts} ];then
      echo "Max attempts reached" >> $LOG_FILE
      exit 1
    fi
    printf '.'
    attempt_counter=$(($attempt_counter+1))
    sleep 5
done

# The migration to the rootless container requires that hooks be regenerated
if [ -f "/var/lib/gitea/regenerate-hooks" ]; then
  echo "Regenerating git hooks" >> $LOG_FILE
  /usr/local/bin/gitea admin regenerate hooks --config ${DATA_MOUNT}/app.ini
  rm /var/lib/gitea/regenerate-hooks
fi

# Setting up crayvcs user, gitea has no way of listing users to check if the
# user already exists, so have to create one and check the return code. Gitea
# issue has been filed: https://github.com/go-gitea/gitea/issues/6001
echo "Creating admin user" >> $LOG_FILE
CRAYVCS_USER=$(</mnt/crayvcs-credentials/vcs_username)
CRAYVCS_PASSWORD=$(</mnt/crayvcs-credentials/vcs_password)
CRAYVCS_USER_EMAIL="${CRAYVCS_USER}@mgmt-plane-nmn.local"
cd ${DATA_MOUNT}/custom
echo "Running in `pwd`" >> $LOG_FILE
# The password argument must go last because if it happens to begin with
# a dash, it causes problems if it is not last.
/usr/local/bin/gitea admin user create \
    --config ${DATA_MOUNT}/app.ini \
    --username ${CRAYVCS_USER} \
    --admin \
    --must-change-password=false \
    --email "${CRAYVCS_USER_EMAIL}" \
    --password="${CRAYVCS_PASSWORD}" &>> $LOG_FILE

RESULT=$?
if [ $RESULT == 0 ]; then
  # Leave a breadcrumb that the user has been created
  echo "admin user '${CRAYVCS_USER}' created" >> $LOG_FILE
  touch ${DATA_MOUNT}/gitea/crayvcs_user_created
  echo `date` >> ${DATA_MOUNT}/gitea/crayvcs_user_created
else
  echo "User creation failed OR admin user '${CRAYVCS_USER}' has previously been created" >> $LOG_FILE
fi
