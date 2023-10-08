"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.client import Ec2
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class Vpc(Ec2):
    """
    Class that represents an AWS vpc.
    """

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.id = None
        self.state = None
        self.cidr = None

    def load(self) -> bool:
        """
        Loads the vpc data, throws an error if more than 1 are found,
        returns True if a vpc is found, False otherwise.
        """

        response = self.ec2.describe_vpcs(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        self.name,
                    ],
                },
            ],
        ).get("Vpcs")

        if len(response) > 1:
            # do not allow more vpc with the same name.
            raise AwsException("Found more than 1 vpc!")

        if len(response) == 0:
            return False
        else:
            self.id = response[0].get("VpcId")
            self.state = response[0].get("State")
            self.cidr = response[0].get("CidrBlock")

            return True

    def create(self, cidr: str) -> None:
        """
        Creates a VPC and waits until it's available.
        """

        if self.load() is True:
            # do not allow more vpc with the same name.
            raise AwsException("Vpc already created!")

        try:
            self.id = (
                self.ec2.create_vpc(
                    CidrBlock=cidr,
                    TagSpecifications=[
                        {
                            "ResourceType": "vpc",
                            "Tags": [
                                {"Key": "Name", "Value": self.name},
                            ],
                        }
                    ],
                )
                .get("Vpc")
                .get("VpcId")
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the vpc!")

        waiter = self.ec2.get_waiter("vpc_available")
        waiter.wait(VpcIds=[self.id])

    def delete(self) -> None:
        """
        Deletes the VPC.
        """
        try:
            self.ec2.delete_vpc(VpcId=self.id)
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the vpc!")
