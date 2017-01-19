#!/usr/bin/env python


import sys
import argparse
import requests


def get_public_ip():
    return requests.get('http://ip.42.pl/raw').content


class CloudFlareDNS(object):
    API_URI = "https://api.cloudflare.com/client/v4/"
    DNS_ENDPOINT = "zones/%(zone_id)s/dns_records"

    def __init__(self, api_key, zone_id, email):
        self.api_key = api_key
        self.zone_id = zone_id
        self.email = email
        self.dns_uri = self.API_URI + (
            self.DNS_ENDPOINT % {'zone_id': zone_id})
        self.headers = {"X-Auth-Email": email, "X-Auth-Key": api_key,
                        "Content-Type": "application/json"}

    def get_domain_by_name(self, domain_name):
        domains = requests.get(
            self.dns_uri, headers=self.headers).json()["result"]

        domain_result = None
        for domain in domains:
            if domain["name"] == domain_name:
                domain_result = domain
        if not domain_result:
            raise ValueError("Domain name %s does not exist" % domain_name)

        return domain_result

    def update_dns(self, domain_name):
        domain = self.get_domain_by_name(domain_name)
        curr_pub_ip = get_public_ip()

        if domain["content"] != curr_pub_ip:
            payload = {"type": domain["type"], "name": domain_name,
                       "content": curr_pub_ip, "proxied": domain["proxied"]}
            endpoint = "%s/%s" % (self.dns_uri, domain["id"])
            r = requests.put(endpoint, headers=self.headers, json=payload)
            r.raise_for_status()


def error(msg):
    print(msg)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Update DNS records in CloudFlare.')
    parser.add_argument('-k', '--apikey', help="Your CloudFlare API key")
    parser.add_argument('-d', '--domain', help="Name of your domain")
    parser.add_argument('-z', '--zoneid', help="Your CloudFlare zone id")
    parser.add_argument('-e', '--email', help="Your CloudFlare email")
    args = parser.parse_args()

    if not all([args.apikey, args.domain, args.zoneid, args.email]):
        error("Arguments -k, -d, -z and -e are required.")
    else:
        try:
            client = CloudFlareDNS(args.apikey, args.zoneid, args.email)
            client.update_dns(args.domain)
        except ValueError as ex:
            error(ex.message)
        print("Success")


if __name__ == "__main__":
    main()
