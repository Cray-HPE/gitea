#!/usr/bin/env python
#
# MIT License
#
# (C) Copyright 2020-2022 Hewlett Packard Enterprise Development LP
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

import logging
import os
import time

import kubernetes.config
import oauthlib.oauth2
import requests_oauthlib

VCS_SECRET_DIR = '/mnt/vcs-user-credentials'

DEFAULT_KEYCLOAK_BASE = 'https://keycloak.services:8080/keycloak'

LOGGER = logging.getLogger('vcs-keycloak-setup')


class KeycloakGiteaSetup(object):
    MASTER_REALM_NAME = 'master'
    SHASTA_REALM_NAME = 'shasta'

    def __init__(
            self,
            keycloak_base,
            kc_master_admin_client_id,
            kc_master_admin_username,
            kc_master_admin_password):
        self.keycloak_base = keycloak_base
        self.kc_master_admin_client_id = kc_master_admin_client_id
        self.kc_master_admin_username = kc_master_admin_username
        self.kc_master_admin_password = kc_master_admin_password

        self._kc_master_admin_client_cache = None

    def run(self):
        self._create_gitea_user()

    @property
    def _kc_master_admin_client(self):
        if self._kc_master_admin_client_cache:
            return self._kc_master_admin_client_cache

        kc_master_token_endpoint = (
            '{}/realms/{}/protocol/openid-connect/token'.format(
                self.keycloak_base, self.MASTER_REALM_NAME))

        kc_master_client = oauthlib.oauth2.LegacyApplicationClient(
            client_id=self.kc_master_admin_client_id)

        client = requests_oauthlib.OAuth2Session(
            client=kc_master_client, auto_refresh_url=kc_master_token_endpoint,
            auto_refresh_kwargs={
                'client_id': self.kc_master_admin_client_id,
            },
            token_updater=lambda t: LOGGER.info("Refreshed Keycloak master admin token"))
        client.verify = False
        LOGGER.info("Fetching initial KC master admin token.")
        client.fetch_token(
            token_url=kc_master_token_endpoint,
            client_id=self.kc_master_admin_client_id,
            username=self.kc_master_admin_username,
            password=self.kc_master_admin_password)

        self._kc_master_admin_client_cache = client
        return self._kc_master_admin_client_cache

    def _create_gitea_user(self):
        LOGGER.info("Creating gitea users..")
        username, password = self._load_vcs_user_secret()
        self._create_user(username, password)
        LOGGER.info("Created gitea users.")

    def _load_vcs_user_secret(self):
        try:
            with open('{}/vcs_username'.format(VCS_SECRET_DIR)) as f:
                username = f.read()
            with open('{}/vcs_password'.format(VCS_SECRET_DIR)) as f:
                password = f.read()
            return username, password
        except Exception:
            LOGGER.warning('Expected vcs user secret, but not found')
            raise

    def _create_user(self, username, password):
        url = (
            '{}/admin/realms/{}/users'.format(
                self.keycloak_base, self.SHASTA_REALM_NAME))
        req_body = {
            'username': username,
            'enabled': True,
            'credentials': [
                {
                    'type': 'password',
                    'value': password,
                },
            ]
        }
        response = self._kc_master_admin_client.post(url, json=req_body)
        if response.status_code == 409:
            LOGGER.info("User %r already exists", username)
            return
        response.raise_for_status()
        LOGGER.info("Created user %r", username)


def read_keycloak_master_admin_secrets(
        secret_dir='/mnt/keycloak-master-admin-auth-vol'):
    with open('{}/client-id'.format(secret_dir)) as f:
        client_id = f.read()
    with open('{}/user'.format(secret_dir)) as f:
        user = f.read()
    with open('{}/password'.format(secret_dir)) as f:
        password = f.read()

    return {
        'client_id': client_id,
        'user': user,
        'password': password
    }

def main():
    log_format = "%(asctime)-15s - %(levelname)-7s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    # Load K8s configuration
    kubernetes.config.load_incluster_config()

    keycloak_base = os.environ.get('KEYCLOAK_BASE', DEFAULT_KEYCLOAK_BASE)

    # If this fails, a retry shouldn't make a difference, since it is just
    # reading from files in the mounted keycloak secret. So we do not
    # catch exceptions and instead let them cause failure.
    LOGGER.info("Loading keycloak secrets.")
    kc_master_admin_secrets = read_keycloak_master_admin_secrets()

    ks = KeycloakGiteaSetup(
        keycloak_base=keycloak_base,
        kc_master_admin_client_id=kc_master_admin_secrets['client_id'],
        kc_master_admin_username=kc_master_admin_secrets['user'],
        kc_master_admin_password=kc_master_admin_secrets['password'],
    )

    while True:
        try:
            ks.run()
            break
        except Exception:
            LOGGER.warning(
                'setup of gitea default user in keycloak failed, will try again', exc_info=True)
            time.sleep(10)

    LOGGER.info('gitea user creation complete')


if __name__ == '__main__':
    main()
