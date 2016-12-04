#!/usr/bin/env python
#
# CloudFlare DDNS script.
#
# usage:
#   cloudflare_ddns.py [config]
#
# See README for details
#

import requests
import json
import time
import yaml
import os
import sys
from subprocess import Popen, PIPE

# CloudFlare api url.
CLOUDFLARE_URL = 'https://api.cloudflare.com/client/v4'

# Time-to-live for your A record. This should be as small as possible to ensure
# changes aren't cached for too long and are propogated quickly.  CloudFlare's
# api docs set a minimum of 120 seconds.
TTL = '120'

# DNS record type for your DDNS host. Probably an A record.
RECORD_TYPE = 'A'

# Location of this script.
SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))

# If a command-line argument is provided, use that as the config file.
if len(sys.argv) == 1:
    CONFIG_FILE = os.path.join(SCRIPT_ROOT, "config.yaml")
else:
    CONFIG_FILE = os.path.join(SCRIPT_ROOT, sys.argv[1])


def main():
    if not os.path.isfile(CONFIG_FILE):
        die(
            "Configuration file not found. Please review the README and try "
            "again."
        )

    # Read config file
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.load(f)

    cf_key = config.get('cf_key')
    cf_email = config.get('cf_email')
    cf_domain = config.get('cf_domain')
    cf_subdomain = config.get('cf_subdomain')
    cf_service_mode = config.get('cf_service_mode')
    quiet = config.get('quiet')
    aws_use_ec2metadata = config.get('aws_use_ec2metadata')
    use_dig = config.get('use_dig')

    auth_headers = {
        'X-Auth-Key': cf_key,
        'X-Auth-Email': cf_email,
    }

    ### Discover your public IP address.
    if aws_use_ec2metadata:
      try:
        p = Popen(
            ["ec2metadata", "--public-ip"],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        output, err = p.communicate()
        rc = p.returncode
        public_ip = output.rstrip('\n')
      except:
        die("Failed to query AWS ec2metadata for public IP")
    elif use_dig:
        p = Popen(["dig", "+short", "myip.opendns.com", "@resolver1.opendns.com"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        rc = p.returncode
        public_ip = output.decode().rstrip()
    else:
        public_ip = requests.get("https://ipv4.icanhazip.com/").text.strip()
        # public_ip = '127.0.0.100'

    ### Get zone id for the dns record we want to update
    results = get_paginated_results(
        'GET',
        CLOUDFLARE_URL + '/zones',
        auth_headers,
    )
    cf_zone_id = None
    for zone in results:
        zone_name = zone['name']
        zone_id = zone['id']
        if zone_name == cf_domain:
            cf_zone_id = zone_id
            break
    if cf_zone_id is None:
        raise Exception("Snap, can't find zone '{}'".format(cf_domain))

    ### Get record id for the record we want to update
    if cf_subdomain == '':
        target_name = cf_domain
    else:
        target_name = cf_subdomain + '.' + cf_domain
    results = get_paginated_results(
        'GET',
        CLOUDFLARE_URL + '/zones/' + cf_zone_id + '/dns_records',
        auth_headers,
    )
    cf_record_obj = None
    for record in results:
        record_id = record['id']
        record_name = record['name']
        if record_name == target_name:
            cf_record_obj = record
            break
    if cf_record_obj is None:
        raise Exception("Snap, can't find record '{}'".format(target_name))

    if not quiet:
        print(json.dumps(cf_record_obj, indent=4))

    ### Update the record
    current_record_ip = cf_record_obj['content']
    if current_record_ip == public_ip:
        # If this record already has the correct IP, we return early
        # and don't do anything.
        if not quiet:
            log('unchanged', '{}, {}'.format(target_name, public_ip))
        return

    cf_record_obj['content'] = public_ip
    r = requests.put(
        CLOUDFLARE_URL
            + '/zones/'
            + cf_zone_id
            + '/dns_records/'
            + cf_record_obj['id'],
        headers=auth_headers,
        json=cf_record_obj
    )
    status_was_error = False
    if r.status_code < 200 or r.status_code > 299:
        log(
            'error',
            "CloudFlare returned an unexpected status code: {}, for "
            "dns_records update request."
            .format(r.status_code)
        )
        status_was_error = True
    response = r.json()
    if response["errors"] or status_was_error:
        die("Updating record failed with the response: '{}'".format(
            json.dumps(response)
        ))
    else:
        log('updated', "{}, {}".format(target_name, public_ip))


    return


def die(msg):
    log('error', msg)
    raise Exception(msg)


def get_paginated_results(method, url, auth_headers):
    """
    Executes the cloudflare api call, fetches all pages and returns the
    concatenated result array.
    """

    results = []
    page = 0
    total_pages = None
    while page != total_pages:
        page += 1
        r = requests.request(
            method,
            url,
            params={'page': page},
            headers=auth_headers
        )

        if r.status_code < 200 or r.status_code > 299:
            die(
                "CloudFlare returned an unexpected status code: {}, for "
                "request: {}"
                .format(
                    r.status_code,
                    url
                )
            )

        response = r.json()
        results.extend(response['result'])
        total_pages = response['result_info']['total_pages']
    return results



# TODO use a real logging framework.
def log(status, message=''):
    print(
        "{date}, {status:>10}, '{message}'".format(
            date=time.ctime(),
            status=status,
            message=message
        )
    )
    return


if __name__ == '__main__':
    main()
