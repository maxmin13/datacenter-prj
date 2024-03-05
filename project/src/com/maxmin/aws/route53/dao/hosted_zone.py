"""
Created on Apr 10, 2023

@author: vagrant
"""
import re

from com.maxmin.aws.client import Route53


class HostedZone(Route53):
    """
    classdocs
    """

    def __init__(self, registered_domain):
        super().__init__()
        self.registered_domain = registered_domain
        self.id = None

    def load(self) -> bool:
        """
        Loads the hosted zone data, returns True if a hosted zone is found,
        False otherwise.
        """

        # returns a list, but the record which has the DNSName is listed first.
        # if the record doesn't exist, it'll return the next record in some alphabetical order
        zones = self.route53.list_hosted_zones_by_name(
            DNSName=self.registered_domain, MaxItems="1"
        ).get("HostedZones")

        fqdn_pattern = re.compile(
            self.registered_domain + "[.]?"
        )  # fully qualified domain name

        if len(zones) > 0:
            zone = zones[0]
            if fqdn_pattern.match(zone.get("Name")):
                self.id = zone.get("Id")

                return True

        return False
