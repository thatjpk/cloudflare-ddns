import requests
import json
import time
import yaml
import os
import sys

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

# Location of the config file.
CONFIG_FILE = os.path.join(SCRIPT_ROOT, sys.argv[1])


def main():
    # Read config file
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.load(f)
    cf_key = config.get('cf_key')
    cf_email = config.get('cf_email')
    cf_domain = config.get('cf_domain')
    cf_subdomain = config.get('cf_subdomain')
    cf_service_mode = config.get('cf_service_mode')

    # Discover your public IP address.
    public_ip = requests.get("http://icanhazip.com/").text.strip()

    # Discover the record_id for the record we intend to update.
    cf_params = {
        'a': 'rec_load_all',
        'tkn': cf_key,
        'email': cf_email,
        'z': cf_domain,
        'o': 0
    }

    record_id = None
    while not record_id:  # Getting all records can return a paginated result, so we do a while.
        cf_response = requests.get(CLOUDFLARE_URL, params=cf_params)
        if cf_response.status_code < 200 or cf_response.status_code > 299:
            raise Exception("CloudFlare returned an unexpected status code: %s" % response.status_code)

        response = json.loads(cf_response.text)
        for record in response["response"]["recs"]["objs"]:
            if record["type"] == RECORD_TYPE and \
               (record["name"] == cf_subdomain or record["name"] == str(cf_subdomain + "." + cf_domain)):

                # If this record already has the correct IP, we return early and don't do anything.
                if record["content"] == public_ip:
                    return

                record_id = record["rec_id"]

        # We didn't see a result. Check if the response was paginated and if so, call another page.
        if not record_id:
            if response["response"]["recs"]["has_more"]:
                cf_params["o"] = response["response"]["recs"]["count"]  # Set a new start point
            else:
                raise Exception("Can't find an existing %s record matching the name '%s'" % (RECORD_TYPE, cf_subdomain))


    # Now we've got a record_id and all the good stuff to actually update the record, so let's do it.
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
        raise Exception("CloudFlare returned an unexpected status code: %s" % response.status_code)
    response = json.loads(cf_response.text)

    if response["result"] == "success":
        print "%s has been successfully updated to point to the IP %s" % (cf_subdomain, public_ip)
    else:
        raise Exception("Updating record failed with the result '%s'" % response["result"])


if __name__ == '__main__':
    main()
