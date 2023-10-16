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
        name: str,
        registered_domain: str,
        public_ip: str,
    ) -> bool:
        """
        Checks if a DNS record exists in the hosted zone.
        """

        dns_name = self.__build_dns_domain(name, registered_domain)

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
        name: str,
        registered_domain: str,
        public_ip: str,
    ) -> None:
        """
        Creates a DNS record.
        """
        try:
            dns_name = self.__build_dns_domain(name, registered_domain)

            hosted_zone = HostedZone(registered_domain)
            hosted_zone.load()
            record = Record(dns_name, hosted_zone.id)
            record.create(public_ip)

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the DNS record!")

    def delete_record(
        self,
        name: str,
        registered_domain: str,
        public_ip: str,
    ) -> None:
        """
        Deletes a DNS record.
        """
        try:
            dns_name = self.__build_dns_domain(name, registered_domain)

            hosted_zone = HostedZone(registered_domain)
            hosted_zone.load()
            record = Record(dns_name, hosted_zone.id)
            record.delete(public_ip)

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the DNS record!")

    def __build_dns_domain(
        self,
        name: str,
        registered_domain: str,
    ) -> str:
        return name + "." + registered_domain
