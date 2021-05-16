#!/usr/bin/python
# Copyright 2019, 2021 Hewlett Packard Enterprise Development LP
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

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: gitea_repo
short_description: Creates and deletes Repositories in Gitea.
version_added: "2.5"
description:
    - Creates or deletes Gitea repositories

options:
    name:
        description:
            - Name of the repository
        required: true
    org:
        description:
            - Name of the organization which owns/will own the repo
            - Do not specify both org and user
        required: false
    user:
        description:
            - Name of the user which owns/will own the repo
            - Do not specify both org and user
        required: false
    description:
        description:
            - Description of the repository to create
        required: false
    auto_init:
        description:
            - Should the repository be auto-initialized when created
        required: false
        default: false
        type: bool
    gitignores:
        description:
            - Gitignores to use
        required: false
    license:
        description:
            - License to use
        required: false
    private:
        description:
            - Whether the repository is private
        type: bool
        required: false
        default: false
    readme:
        description:
            - Readme of the repository to create
        required: false
    login_user:
        description:
            - Username of the user doing the operation
            - Required if using basic auth
        required: false
    login_password:
        description:
            - Password of the login_user.
            - Required if using basic auth
        required: false
        no_log: true
    api_token:
         description:
             - If using token-based auth, the token to use
             - Not required if using basic auth
         required: false
         no_log: true
    gitea_url:
         description:
             - Base Url to the gitea API server
         required: true
    state:
         description:
             - State of the repository, either present (create it) or absent (delete it)
         required: false
         default: present

author:
    - Randy Kleinman (rkleinman@cray.com)
'''

EXAMPLES = '''
# Create a minimal repo with basic auth
- name: Create a public repo for admin_user
  gitea_repo:
    name: my_repo
    user: admin_user
    login_user: admin_user
    login_password: mypassword
    gitea_url: https://my-gitea.example.com/api/v1

# Create a repo in the my_org organization with token auth
- name: Create a repo
  gitea_repo:
    name: my_repo
    org: my_org
    api_token: d507e44cdbfe1c48b80000afc12256ce601f3648
    state: present
    gitea_url: https://my-gitea.example.com/api/v1

# Delete a personal repo using basic auth
- name: remove a repo
  gitea_repo:
    name: my_repo
    user: admin_user
    login_user: admin_user
    login_password: mypassword
    state: absent
    gitea_url: https://my-gitea.example.com/api/v1
'''

RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "Success"
json:
  description: JSON parsed response from the server, if any was sent.
  returned: success
  type: dict
error:
  description: The error message returned by the API, if unexpected errors occur
  returned: failed
  type: str
  sample: "401: Unauthorized"
'''
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

import json
from base64 import b64encode


def _add_auth_headers(headers, module):
    """ Add auth headers depending on the auth type """
    if module.params['api_token']:  # token
        headers['Authorization'] = 'token {}'.format(module.params['api_token'])
    else:  # basic
        credentials = module.params['login_user'] + ':' + module.params['login_password']
        headers['Authorization'] = 'Basic {}'.format(b64encode(credentials))
    return headers


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        org=dict(type='str', required=False),
        user=dict(type='str', required=False),
        description=dict(type='str', required=False),
        auto_init=dict(type='bool', required=False, default=False),
        gitignores=dict(type='str', required=False),
        license=dict(type='str', required=False),
        private=dict(type='bool', required=False, default=False),
        readme=dict(type='str', required=False),
        api_token=dict(type='str', required=False, no_log=True),
        login_user=dict(type='str', required=False),
        login_password=dict(type='str', required=False, no_log=True),
        gitea_url=dict(type='str', required=True),
        state=dict(type='str', default="present", choices=["absent", "present"]),
    )

    mutually_exclusive=[
        ['api_token', 'login_user'],
        ['api_token', 'login_password'],
        ['org', 'user'],
    ]

    required_together=[
        ['login_user', 'login_password'],
    ]

    required_one_of=[
        ['api_token', 'login_user'],
        ['api_token', 'login_password'],
        ['org', 'user']
    ]

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        msg='',
        json='',
        error='',
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=mutually_exclusive,
        required_together=required_together,
        required_one_of=required_one_of,
        supports_check_mode=False,
    )

    repo_fields = {
        'name': module.params['name'],
        'auto_init': module.params['auto_init'] or False,
        'description': module.params['description'] or None,
        'gitignores': module.params['gitignores'] or None,
        'license': module.params['license'] or None,
        'private': module.params['private'] or False,
        'readme': module.params['readme'] or None,
    }

    org = module.params['org'] or None
    user = module.params['user'] or None
    gitea_url = module.params['gitea_url']
    login_user = module.params['login_user']
    state = module.params['state']
    headers = {'Content-type': 'application/json'}
    _add_auth_headers(headers, module)

    # Set urls
    if org:
        create_url = '{}/org/{}/repos'.format(gitea_url, org) # org repo create
        delete_url = '{}/repos/{}/{}'.format(gitea_url, org, repo_fields['name'])  # org repo delete
    else:
        create_url = '{}/user/repos'.format(gitea_url)  # user repo create
        delete_url = '{}/repos/{}/{}'.format(gitea_url, user, repo_fields['name'])  # user repo delete

    # Create a Repo
    if state == 'present':
        # Try creating it, if a 409 is returned it already exists. Gitea does
        # not allow patching, so if it exists, that has to be good enough.
        # See: https://github.com/go-gitea/gitea/issues/5960 for patching RFE.
        url = create_url
        method = 'POST'
        data=module.jsonify({k : v for (k, v) in repo_fields.items() if v})

    # Delete a repo
    else:
        url = delete_url
        method = 'DELETE'
        data = {}

    # Make the request
    resp, info = fetch_url(module, url, headers=headers, method=method, data=data)

    status_code = info["status"]
    result.update(info)

    # Failure status code
    if status_code >= 400:
        # Deleting a repo that doesn't exist
        if state == 'absent' and status_code == 404:
            result['msg'] = "Repository {} removed.".format(repo_fields['name'])
            module.exit_json(**result)

        # Creating a repo that already exists
        if state == 'present' and status_code == 409:
            result['msg'] = "Repository {} exists.".format(repo_fields['name'])
            module.exit_json(**result)

        # Something else went wrong
        else:
            try:
                result['error'] = info['msg']
                result['msg'] = json.loads(info['body'])['message']
                module.fail_json(**result)
            except:
                pass
            module.fail_json(**info)

    # Success
    else:
        body = resp.read()
        result['json'] = json.loads(body) if body else {}
        result['changed'] = True
        result['msg'] = "Repository {} was {}.".format(repo_fields['name'],
                                                       ('deleted', 'created')[state == 'present'])

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
