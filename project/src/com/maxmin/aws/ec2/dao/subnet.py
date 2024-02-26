"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.client import Ec2
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class Subnet(Ec2):
    """
    Class that represents an AWS subnet.
    """

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.id = None
        self.cidr = None
        self.az = None
        self.vpc_id = None

    def load(self) -> bool:
        """
        Loads the subnet data, throws an error if more than 1 are found,
        returns True if a subnet is found, False otherwise.
        """

        response = self.ec2.describe_subnets(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        self.name,
                    ],
                },
            ],
        ).get("Subnets")

        if len(response) > 1:
            # do not allow more subnets with the same name.
            raise AwsException("Found more than 1 subnet!")

        if len(response) == 0:
            return False
        else:
            self.id = response[0].get("SubnetId")
            self.cidr = response[0].get("CidrBlock")
            self.az = response[0].get("AvailabilityZone")
            self.vpc_id = response[0].get("VpcId")

            return True

    def create(self, az: str, cidr: str, vpc_id: str) -> None:
        """
        Creates a subnet and waits until it's available.
        """

        if self.load() is True:
            # do not allow more subnets with the same name.
            raise AwsException("Subnet already created!")

        try:
            self.id = (
                self.ec2.create_subnet(
                    TagSpecifications=[
                        {
                            "ResourceType": "subnet",
                            "Tags": [
                                {"Key": "Name", "Value": self.name},
                            ],
                        }
                    ],
                    AvailabilityZone=az,
                    CidrBlock=cidr,
                    VpcId=vpc_id,
                )
                .get("Subnet")
                .get("SubnetId")
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the subnet!")

        waiter = self.ec2.get_waiter("subnet_available")
        waiter.wait(SubnetIds=[self.id])

    def delete(self) -> None:
        """
        Deletes the subnet.
        """
        try:
            self.ec2.delete_subnet(SubnetId=self.id)
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the subnet!")
