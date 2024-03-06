"""
Created on Apr 9, 2023

@author: vagrant
"""
import re

from com.maxmin.aws.client import Route53Dao
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class RecordDao(Route53Dao):
    """
    classdocs
    """

    def __init__(self, domain: str, hosted_zone_id: str):
        super().__init__()
        self.hosted_zone_id = hosted_zone_id
        self.domain = domain
        self.ip_address = None
        self.type = None

    def load(self) -> bool:
        """
        Loads the DNS record data, returns True if a record is found, False
        otherwise.
        """

        records = self.route53.list_resource_record_sets(
            HostedZoneId=self.hosted_zone_id
        ).get("ResourceRecordSets")

        fqdn_pattern = re.compile(
            self.domain + "[.]?"
        )  # fully qualified domain name

        if len(records) > 0:
            for record in records:
                if fqdn_pattern.match(record.get("Name")):
                    self.type = record.get("Type")
                    self.ip_address = record.get("ResourceRecords")[0].get(
                        "Value"
                    )

                    return True

        return False

    def create(self, ip_address: str) -> None:
        """
        Creates a route53 DNS record.
        """

        if self.load() is True:
            # do not allow more records with the same name.
            raise AwsException("Record already created!")

        try:
            response = (
                self.route53.change_resource_record_sets(
                    HostedZoneId=self.hosted_zone_id,
                    ChangeBatch={
                        "Changes": [
                            {
                                "Action": "CREATE",
                                "ResourceRecordSet": {
                                    "Name": self.domain,
                                    "Type": "A",
                                    "TTL": 300,
                                    "ResourceRecords": [{"Value": ip_address}],
                                },
                            }
                        ]
                    },
                )
                .get("ChangeInfo")
                .get("Id")
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the record!")

        waiter = self.route53.get_waiter("resource_record_sets_changed")
        waiter.wait(Id=response)

    def delete(self, ip_address: str) -> None:
        """
        Deletes a route53 DNS record.
        """

        try:
            self.route53.change_resource_record_sets(
                HostedZoneId=self.hosted_zone_id,
                ChangeBatch={
                    "Changes": [
                        {
                            "Action": "DELETE",
                            "ResourceRecordSet": {
                                "Name": self.domain,
                                "Type": "A",
                                "TTL": 300,
                                "ResourceRecords": [{"Value": ip_address}],
                            },
                        }
                    ]
                },
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the record!")
