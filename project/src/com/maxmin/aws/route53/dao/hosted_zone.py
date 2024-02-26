"""
Created on Apr 10, 2023

@author: vagrant
"""

from com.maxmin.aws.client import Route53
from com.maxmin.aws.exception import AwsException


class HostedZone(Route53):
    """
    classdocs
    """

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.id = None

    def load(self) -> bool:
        """
        Loads the hosted zone data, returns True if a hosted zone is found,
        False otherwise.
        """

        response = self.route53.list_hosted_zones_by_name(
            DNSName=self.name,
        ).get("HostedZones")

        if len(response) > 1:
            raise AwsException("Found more than 1 hosted zone!")

        if len(response) == 0:
            return False
        else:
            self.id = response[0].get("Id")

            return True
