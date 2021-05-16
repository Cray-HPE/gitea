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
module: gitea_org
short_description: Creates, updates, deletes Organizations in Gitea.
version_added: "2.5"
description:
    - Creates, updates, and deletes Gitea organizations.

options:
    username:
        description:
            - Name of the organization
        required: true
    description:
        description:
            - Description of the organization
        required: false
    full_name:
        description:
            - Full display name of the organization
        required: false
    location:
        description:
            - Location of the organization
        required: false
    website:
        description:
            - Website URL of the organization
        required: false
    login_user:
        description:
            - The gitea user name to create the organizationo
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
             - State of the organization, either present or absent.
         required: false
         default: present

author:
    - Randy Kleinman (rkleinman@cray.com)
'''

EXAMPLES = '''
# Create a minimal organization with basic auth
- name: Create an organization
  gitea_org:
    username: my_org
    login_user: admin_user
    login_password: mypassword
    gitea_url: https://my-gitea.example.com/api/v1

# Create an organization (full options) with token auth
- name: Create an organization
  gitea_org:
    username: my_org
    website: http://my_org.example.com
    description: My Org's Organization in Gitea
    full_name: My Org
    location: Anytown, USA
    api_token: d507e44cdbfe1c48b80000afc12256ce601f3648
    state: present
    gitea_url: https://my-gitea.example.com/api/v1

# Update an organization's full_name with token auth
- name: Create an organization
  gitea_org:
    username: my_org
    full_name: My Org's New Name
    api_token: d507e44cdbfe1c48b80000afc12256ce601f3648
    state: present
    gitea_url: https://my-gitea.example.com/api/v1

# Delete an organization using basic auth
- name: Create an organization
  gitea_org:
    username: my_org
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

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        username=dict(type='str', required=True),
        website=dict(type='str', required=False),
        description=dict(type='str', required=False),
        full_name=dict(type='str', required=False),
        location=dict(type='str', required=False),
        api_token=dict(type='str', required=False, no_log=True),
        login_user=dict(type='str', required=False),
        login_password=dict(type='str', required=False, no_log=True),
        gitea_url=dict(type='str', required=True),
        state=dict(type='str', default="present", choices=["absent", "present"]),
    )

    mutually_exclusive=[
        ['api_token', 'login_user'],
        ['api_token', 'login_password'],
    ]

    required_together=[
        ['login_user', 'login_password'],
    ]

    required_one_of=[
        ['api_token', 'login_user']
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

    org_fields = {
        'username': module.params['username'],
        'website': module.params['website'] or None,
        'description': module.params['description'] or None,
        'full_name': module.params['full_name'] or None,
        'location': module.params['location'] or None
    }

    api_token = module.params['api_token'] or None
    gitea_url = module.params['gitea_url']
    state = module.params['state']
    headers = {'Content-type': 'application/json'}

    # Determine auth method
    if api_token:
        headers['Authorization'] = 'token {}'.format(api_token)
    else:
        credentials = module.params['login_user'] + ':' + module.params['login_password']
        headers['Authorization'] = 'Basic {}'.format(b64encode(credentials))

    # Create/Update an Org
    if state == 'present':
        # Determine if this is a create, or an update. Try to GET it first.
        # If that fails, try to create it, else update it.
        url = '{}/orgs/{}'.format(gitea_url, org_fields['username'])
        method = 'GET'
        resp, info = fetch_url(module, url, headers=headers, method=method)

        # Not found, try creating it
        if info['status'] == 404:
            url = '{}/orgs'.format(gitea_url)
            method = 'POST'
            data=module.jsonify({k : v for (k, v) in org_fields.items() if v})

        # Found, try patching it
        elif info['status'] == 200:
            url = '{}/orgs/{}'.format(gitea_url, org_fields['username'])
            method = 'PATCH'
            data = module.jsonify({k : v for (k, v) in org_fields.items() if v and k != 'username'})

        # Something went wrong
        else:
            module.fail_json(msg="Unable to find the org.", changed=False, error=info['msg'])

    # Delete an org
    else:
        url = '{}/orgs/{}'.format(gitea_url, org_fields['username'])
        method = 'DELETE'
        data = {}

    # Make the request
    resp, info = fetch_url(module, url, headers=headers, method=method, data=data)
    status_code = info["status"]
    result.update(info)

    # Failure status code
    if status_code >= 400:
        result.pop('body')  # loaded in 'msg' field

        # Deleting an org that doesn't exist
        if state == 'absent' and status_code == 404:
            result['msg'] = "Organization {} removed.".format(org_fields['username'])
            module.exit_json(**result)

        # Something else went wrong
        else:
            try:
                result['error'] = info['msg']
                result['msg'] = json.loads(info['body'])['message']
                module.fail_json(**result)
            except:
                pass
            info['new_gitea_url'] = gitea_url
            module.fail_json(**info)

    # Success
    else:
        body = resp.read()
        result['json'] = json.loads(body) if body else {}
        result['changed'] = True
        result['msg'] = "Organization {} was {}.".format(org_fields['username'],
                                                         ('deleted', 'created')[state == 'present'])

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
