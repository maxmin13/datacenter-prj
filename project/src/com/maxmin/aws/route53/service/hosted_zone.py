"""
Created on Apr 2, 2023

@author: vagrant
"""

from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.route53.dao.hosted_zone import HostedZone
from com.maxmin.aws.route53.dao.record import Record


class HostedZoneService(object):
    def check_record_exists(
        self,
        registered_domain: str,
        dns_name: str,
    ) -> bool:
        """
        Checks if a DNS record exists in the hosted zone.
        """

        try:
            hosted_zone = HostedZone(registered_domain)
            hosted_zone.load()
            record = Record(dns_name, hosted_zone.id)
            return record.load()

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the DNS record!")

    def create_record(
        self,
        registered_domain: str,
        dns_name: str,
        public_ip: str,
    ) -> None:
        """
        Creates a DNS record.
        """
        try:
            hosted_zone = HostedZone(registered_domain)
            hosted_zone.load()
            record = Record(dns_name, hosted_zone.id)
            record.create(public_ip)

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the DNS record!")

    def delete_record(
        self,
        registered_domain: str,
        dns_name: str,
        public_ip: str,
    ) -> None:
        """
        Deletes a DNS record.
        """
        try:
            hosted_zone = HostedZone(registered_domain)
            hosted_zone.load()
            record = Record(dns_name, hosted_zone.id)
            record.delete(public_ip)

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the DNS record!")
