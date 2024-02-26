"""
Created on Mar 20, 2023

@author: vagrant
"""

from com.maxmin.aws.client import Ec2
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class RouteTable(Ec2):
    """
    Class that represents an AWS route table.
    """

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.id = None
        self.vpc_id = None

    def load(self) -> bool:
        """
        Loads the route table data, throws an error if more than 1 route table
        are found, returns True if one is found, False otherwise.
        """
        response = self.ec2.describe_route_tables(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        self.name,
                    ],
                },
            ]
        ).get("RouteTables")

        if len(response) > 1:
            # do not allow more route tables with the same name.
            raise AwsException("Found more than 1 route table!")

        if len(response) == 0:
            return False
        else:
            self.id = response[0].get("RouteTableId")
            self.vpc_id = response[0].get("VpcId")

            return True

    def create(self, vpc_id) -> None:
        """
        Creates a route table attached to the vpc.
        """
        if self.load() is True:
            # do not allow more route tables with the same name.
            raise AwsException("Route table already created!")

        try:
            self.id = (
                self.ec2.create_route_table(
                    TagSpecifications=[
                        {
                            "ResourceType": "route-table",
                            "Tags": [
                                {"Key": "Name", "Value": self.name},
                            ],
                        }
                    ],
                    VpcId=vpc_id,
                )
                .get("RouteTable")
                .get("RouteTableId")
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the route table!")

    def delete(self) -> None:
        """
        Deletes the route table.
        """
        try:
            self.ec2.delete_route_table(RouteTableId=self.id)
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the route table!")

    def has_route(self, gate_id: str, destination_cidr: str):
        routes = (
            self.ec2.describe_route_tables(
                RouteTableIds=[
                    self.id,
                ],
            )
            .get("RouteTables")[0]
            .get("Routes")
        )

        for route in routes:
            if route.get("State") == "active":
                if (
                    route.get("GatewayId") == gate_id
                    and route.get("DestinationCidrBlock") == destination_cidr
                ):
                    return True

        return False

    def create_route(self, gate_id: str, destination_cidr: str):
        try:
            self.ec2.create_route(
                DestinationCidrBlock=destination_cidr,
                GatewayId=gate_id,
                RouteTableId=self.id,
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating route!")

    def associate_subnet(self, subnet_id: str):
        try:
            self.ec2.associate_route_table(
                RouteTableId=self.id, SubnetId=subnet_id
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error associating subnet to the route table!")
