cloudflare-ddns
===============


*Deprecated*:  Since I no longer use this I don't have much motivation to deal with issues/PRs.  Feel free to check out [Ethaligan's fork](https://github.com/Ethaligan/cloudflare-ddns).

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

You can install them with `pip` :

	pip install -r requirements.txt

Usage
-----

First, a few assumptions:

  - You have a CloudFlare account.
  - You're using CloudFlare to host DNS for a domain you own.
  - You have an A record in CloudFlare you intend to dynamically update.

To use this utility, create a copy of the `config.yaml.template` file (and
remove .template from the filename).  Create one template per each record / 
domain pair you intend to update.  For example, I might have two configuration
files: `site_naked.yaml` that updates the A record for the naked (no www
prefix) domain site.not, and a second config, `site_www.yaml` that updates the
A record for www.site.not.

To do a one-off update of your DNS record, simply run `python
cloudflare_ddns.py config_file_name.yaml` from your terminal.
The script will determine your public IP address and automatically update the
CloudFlare DNS record along with it.

If the program encounters an issue while attempting to update CloudFlare's 
records, it will print the failure response CloudFlare returns. Check your 
configuration file for accurate information and try again.


Because dynamic IPs can change regularly, it's recommended that you run this
utility periodically in the background to keep the CloudFlare record 
up-to-date.

Just add a line to your [crontab](http://en.wikipedia.org/wiki/Cron) and let
cron run it for you at a regular interval.

    # Every 15 minutes, check the current public IP, and update the A record on CloudFlare.
    */15 * * * * /path/to/code/cloudflare_ddns.py /path/to/code/config.yaml >> /var/log/cloudflare_ddns.log

This example will update the record every 15 minutes.  You'll want to be sure
that you insert the correct paths to reflect were the codebase is located.
The redirection (`>>`) to append to a log file is optional, but handy for
debugging if you notice the DNS record is not staying up-to-date.  The script
tries to print something useful to stdout any time it runs. If you find the
"unchanged" messages too chatty, set quiet to true in the config and stdout
will only get messages when the IP actually changed, or when there's an error.

If you want to learn more about the CloudFlare API, you can read on
[here](http://www.cloudflare.com/docs/client-api.html).

Credits and Thanks
------------------

 - [CloudFlare](https://www.cloudflare.com/) for having an API and otherwise
   generally being cool.
 - [icanhazip.com](http://icanhazip.com/) for making grabbing your public IP
    from a script super easy.

