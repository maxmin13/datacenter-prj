"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.client import Ec2
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class InternetGateway(Ec2):
    """
    Class that represents an AWS Internet gateway used by the subnets to reach
    the Internet.
    """

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.id = None
        self.vpc_id = None

    def load(self) -> bool:
        """
        Loads the Internet gateway data, throws an error if more than 1 are
        found and if it's attached to more than one vpc, returns True if one is
        found, False otherwise.
        """

        response = self.ec2.describe_internet_gateways(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        self.name,
                    ],
                },
            ]
        ).get("InternetGateways")

        if len(response) > 1:
            raise AwsException("Found more than 1 Internet gateway!")

        if len(response) == 1 and len(response[0].get("Attachments")) > 1:
            raise AwsException(
                "The Internet gateway is attached to more vcps!"
            )

        if len(response) == 0:
            return False
        else:
            self.id = response[0].get("InternetGatewayId")

        # gateway must be attached to only one vpc.
        attachments = response[0].get("Attachments")

        if len(attachments) > 1:
            raise AwsException(
                "Internet gateway is attached to more than one vpc!"
            )
        elif len(attachments) == 1:
            self.vpc_id = response[0].get("Attachments")[0].get("VpcId")

        return True

    def create(self) -> None:
        """
        Creates an Internet gateway and waits until it exists.
        """

        if self.load() is True:
            raise AwsException("Internet gateway already created!")

        try:
            self.id = (
                self.ec2.create_internet_gateway(
                    TagSpecifications=[
                        {
                            "ResourceType": "internet-gateway",
                            "Tags": [
                                {"Key": "Name", "Value": self.name},
                            ],
                        }
                    ],
                )
                .get("InternetGateway")
                .get("InternetGatewayId")
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the internet gateway!")

        waiter = self.ec2.get_waiter("internet_gateway_exists")
        waiter.wait(InternetGatewayIds=[self.id])

    def delete(self) -> None:
        """
        Deletes the Internet gateway.
        """
        try:
            self.ec2.delete_internet_gateway(InternetGatewayId=self.id)
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the Internet gateway!")

    def attach_to(self, vpc_id: str):
        """
        Attaches the Internet gateway to a VPC,
        enabling connectivity between the Internet and the VPC.
        """
        try:
            self.ec2.attach_internet_gateway(
                InternetGatewayId=self.id, VpcId=vpc_id
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException(
                "Error attaching the Internet gateway to the vpc!"
            )

    def detach_from(self, vpc_id: str):
        """
        Detaches the Internet gateway from a VPC, disabling connectivity between
        the Internet and the VPC..
        """

        try:
            self.ec2.detach_internet_gateway(
                InternetGatewayId=self.id, VpcId=vpc_id
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException(
                "Error detaching the Internet gateway to the vpc!"
            )

    def is_attached_to(self, vpc_id: str):
        """
        Checks if the gateway is attached to a vpc.
        """

        attachments = (
            self.ec2.describe_internet_gateways(
                InternetGatewayIds=[
                    self.id,
                ]
            )
            .get("InternetGateways")[0]
            .get("Attachments")
        )

        for attachment in attachments:
            if attachment.get("State") == "available":
                if attachment.get("VpcId") == vpc_id:
                    return True

        return False
