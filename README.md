cloudflare-ddns
===============

Introduction
------------

A script for dynamically updating a CloudFlare DNS record.  I use CloudFlare
to host DNS for a domain and I wanted to point an A record in that domain to
a host who's IP address changes occasionally.  CloudFlare has an API to do this,
so this happened.

Dependencies
------------

You'll need a python interpreter and the following libraries:

 - [PyYAML](https://bitbucket.org/xi/pyyaml) (`pip install pyyaml`)
 - [Requests](http://docs.python-requests.org/en/latest/) (`pip install
   requests`)

Usage
-----

First, a few assumptions:

  - You have a CloudFlare account.
  - You're using CF to host DNS for a domain you own.
  - You have an A record in CF you intend to dynamically update.

Now, to use this script you'll want to fill out the configuration file. Make a 
copy of `config.yaml.template` named `config.yaml`, then fill out the options in 
`config.yaml`.  The comments in the file make it fairly self explanatory.

Now to do a one-off update of your DNS record, simply run `cloudflare_ddns.py`
from your terminal.  It'll get your public IP address, then update the 
CloudFlare DNS record with it. Easy!  (In fact, you should probably do this once
to test that your config file is correct.)  You should see something like this:

    jpk@truth:~/code/cloudflare-ddns$ ./cloudflare_ddns.py 
    Tue Oct  8 22:09:00 2013, success, 123.45.67.89
    jpk@truth:~/code/cloudflare-ddns$ 

If it fails, it'll print the failure response CloudFlare returns. Check your
`config.yaml` and try again.


If you're like me, though, you probably want it to run periodically in the
background to keep the record up-to-date as your public IP address changes.
Just add a line to your [crontab](http://en.wikipedia.org/wiki/Cron) and let
cron run it for you.  My crontab has a line in it like this:

    # Every 15 minutes, check public ip, and update a record on cloudflare.
    */15 * * * * ~/code/cloudflare-ddns/cloudflare-ddns.py >> ~/code/cloudflare-ddns/logs/log.txt

That will update the record every 15 minutes.  You'll want the paths there to
match up with wherever you checked this repo out.  The redirection to append to
a log file is optional, but handy for debugging if you notice the DNS record
isn't staying up-to-date or something.

Getting the CloudFlare Record ID
--------------------------------

The only tricky thing about the configuration is `cf_record_id`.  This is
CloudFlare's id for the DNS record you want to update.  You'll need to make a
call to their API to find out what this is. You can use this command
to make that call:

    curl https://www.cloudflare.com/api_json.html \
        -d 'a=rec_load_all' \
        -d 'tkn=368812311fb987a376a39e58bc0793ae18708' \
        -d 'email=_@jpk.is' \
        -d 'z=jpk.is' | python -mjson.tool

This should pretty-print a bunch of JSON, part of which will be a list of
objects representing DNS records in your zone.  They look like this:

    ...
    {
        "auto_ttl": 0, 
        "content": "123.45.67.89", 
        "display_content": "123.45.67.89", 
        "display_name": "ddns", 
        "name": "ddns.domain.com", 
        "prio": null, 
        "props": {
            "cf_open": 1, 
            "cloud_on": 0, 
            "expired_ssl": 0, 
            "expiring_ssl": 0, 
            "pending_ssl": 0, 
            "proxiable": 1, 
            "ssl": 0, 
            "vanity_lock": 0
        }, 
        "rec_id": "12345678", 
        "rec_tag": "[some long hex value]", 
        "service_mode": "0", 
        "ssl_expires_on": null, 
        "ssl_id": null, 
        "ssl_status": null, 
        "ttl": "120", 
        "ttl_ceil": 86400, 
        "type": "A", 
        "zone_name": "domain.com"
    },
    ...

Find the one with a `name` field that matches the host you're wanting to update,
and the `rec_id` field is the record id you want to put in your config.
(In this case "ddns.domain.com" is the one we're looking for, and it has a
record id of "12345678".)

If you want to learn more about the CloudFlare API, you can read on
[here](http://www.cloudflare.com/docs/client-api.html).

Credits and Thanks
------------------

 - [CloudFlare](https://www.cloudflare.com/) for having an API and otherwise
   generally being cool.
 - [jsonip.com](http://jsonip.com/) for making grabbing your public IP from a
   script super easy. Put together by [@geuis](https://twitter.com/geuis). Go
   to his twitter and shower him with praise.

