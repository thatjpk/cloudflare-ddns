#!/usr/bin/env python
#
# Ghetto dynamic dns using cloudflare's api.
#
import requests
import json
import time
import yaml


# CloudFlare api url.
CLOUDFLARE_URL = 'https://www.cloudflare.com/api_json.html'

# jsonip api url.
JSONIP_URL = 'http://jsonip.com'

# Time-to-live for your A record. This should be as small as possible to ensure
# changes aren't cached for too long and are propogated quickly.  CloudFlare's
# api docs set a minimum of 120 seconds.
TTL = '120'

# CloudFlare service mode. This enables/disables CF's traffic acceleration.
# Enabled (orange cloud) is 1. Disabled (grey cloud) is 0.
SERVICE_MODE = 0

# DNS record type for your DDNS host. Probably an A record.
RECORD_TYPE = 'A'


def main():
    # Read config file
    with open('./config.yaml', 'r') as f:
        config = yaml.load(f)
    cf_key = config.get('cf_key')
    cf_email = config.get('cf_email')
    cf_domain = config.get('cf_domain')
    cf_subdomain = config.get('cf_subdomain')
    cf_record_id = config.get('cf_record_id')

    # Discover your public IP address.
    public_ip = requests.get(JSONIP_URL).json['ip']

    # Prepare request to cloudflare api, updating your A record.
    cf_params = {
        'a': 'rec_edit',
        'tkn': cf_key,
        'id': cf_record_id,
        'email': cf_email,
        'z': cf_domain,
        'type': RECORD_TYPE,
        'ttl': TTL,
        'name': cf_subdomain,
        'content': public_ip,
        'service_mode': SERVICE_MODE
    }

    # Make request, collect response.
    cf_response = requests.get(CLOUDFLARE_URL, params=cf_params)

    # Print success/fail log message using response.
    result = cf_response.json['result']
    date = time.ctime()
    if result == 'success':
        print '{date}, success, {ip}'.format(date=date, ip=public_ip)
    else:
        response = json.dumps(cf_response.json)
        print '{date}, fail, {response}'.format(date=date, response=response)

    return


if __name__ == '__main__':
    main()
