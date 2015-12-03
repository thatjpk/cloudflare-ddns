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
CLOUDFLARE_URL = 'https://www.cloudflare.com/api_json.html'

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
    now = time.ctime()

    if not os.path.isfile(CONFIG_FILE):
        msg = \
            "Configuration file not found. Please review the README and try " \
            "again."
        log(now, 'error', '(no conf)', '(no conf)', msg)
        raise Exception(msg)

    # Read config file
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.load(f)

    cf_key = config.get('cf_key')
    cf_email = config.get('cf_email')
    cf_domain = config.get('cf_domain')
    cf_subdomain = config.get('cf_subdomain')
    cf_service_mode = config.get('cf_service_mode')
    quiet = 'true' == config.get('quiet')
    aws_use_ec2metadata = config.get('aws_use_ec2metadata')

    # Discover your public IP address.
    if aws_use_ec2metadata:
      try:
        p = Popen(["ec2metadata", "--public-ip"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        rc = p.returncode
        public_ip = output.rstrip('\n')
      except:
        msg = "Failed to query AWS ec2metadata for public IP"
        log(now, 'critical', '(no conf)', '(no conf)', msg)
        raise Exception(msg)
    else:
      public_ip = requests.get("http://ipv4.icanhazip.com/").text.strip()


    # Discover the record_id for the record we intend to update.
    cf_params = {
        'a': 'rec_load_all',
        'tkn': cf_key,
        'email': cf_email,
        'z': cf_domain,
        'o': 0
        }

    # If the config sets empty string as the cf_subdomain, then we don't want
    # the leading '.'
    if cf_subdomain is '':
        target_name = cf_domain
    else:
        target_name = str(cf_subdomain + '.' + cf_domain)
    # Results may be paginated, so loop over each page.
    record_id = None
    while not record_id:
        cf_response = requests.get(CLOUDFLARE_URL, params=cf_params)
        if cf_response.status_code < 200 or cf_response.status_code > 299:
            msg = "CloudFlare returned an unexpected status code: {}".format(
                cf_response.status_code
                )
            log(now, 'error', target_name, public_ip, msg)
            raise Exception(msg)

        response = json.loads(cf_response.text)
        for record in response["response"]["recs"]["objs"]:
            if (
                record["type"] == RECORD_TYPE and \
                (
                    record["name"] == cf_subdomain or \
                    record["name"] == target_name
                    )
                ):
                # If this record already has the correct IP, we return early
                # and don't do anything.
                if record["content"] == public_ip:
                    if not quiet:
                        log(now, 'unchanged', target_name, public_ip)
                    return

                record_id = record["rec_id"]

        # We didn't see a result. Check if the response was paginated and if
        # so, call another page.
        if not record_id:
            if response["response"]["recs"]["has_more"]:
                # Set a new start point
                cf_params["o"] = response["response"]["recs"]["count"] 
            else:
                msg = \
                    "Can't find an existing {} record matching the " \
                    "name '{}'".format(
                        RECORD_TYPE, target_name
                        )
                log(now, 'error', target_name, public_ip, msg)
                raise Exception(msg)

    # Now we've got a record_id and all the good stuff to actually update the
    # record, so let's do it.

    cf_params = {
        'a': 'rec_edit',
        'tkn': cf_key,
        'id': record_id,
        'email': cf_email,
        'z': cf_domain,
        'type': RECORD_TYPE,
        'ttl': TTL,
        'name': cf_subdomain,
        'content': public_ip,
        'service_mode': cf_service_mode
        }

    cf_response = requests.get(CLOUDFLARE_URL, params=cf_params)
    if cf_response.status_code < 200 or cf_response.status_code > 299:
        msg = "CloudFlare returned an unexpected status code: {}".format(
            response.status_code
            )
        log(now, 'error', target_name, public_ip, msg)
        raise Exception(msg)
    response = json.loads(cf_response.text)

    if response["result"] == "success":
        log(now, 'updated', target_name, public_ip)
    else:
        msg = "Updating record failed with the result '{}'".format(
            response["result"]
            )
        log(now, 'error', target_name, public_ip, msg)
        raise Exception(msg)

    return


# TODO use a real logging framework.
def log(timestamp, status, subdomain, ip_address, message=''):
    print(
        "{date}, {status:>10}, {a:>10}, {ip}, '{message}'".format(
            date=timestamp,
            status=status,
            a=subdomain,
            ip=ip_address,
            message=message
            )
        )
    return


if __name__ == '__main__':
    main()
