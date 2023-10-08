"""
Created on Mar 23, 2023

@author: vagrant
"""

import os
import stat

import boto3
from botocore.exceptions import ClientError

from com.maxmin.aws.constants import ProjectDirectories
from comtest.maxmin.exception import TestException


class TestUtils(object):
    """
    Utilities methods to use in tests
    """

    __test__ = False

    def __init__(self):
        self.ec2 = boto3.client("ec2")
        self.route53 = boto3.client("route53")

    def create_vpc(self, name: str, cidr: str):
        vpc_id = (
            self.ec2.create_vpc(
                CidrBlock=cidr,
                TagSpecifications=[
                    {
                        "ResourceType": "vpc",
                        "Tags": [
                            {"Key": "Name", "Value": name},
                        ],
                    }
                ],
            )
            .get("Vpc")
            .get("VpcId")
        )

        return vpc_id

    def describe_vpc(self, vpc_id: str):
        response = self.ec2.describe_vpcs(
            VpcIds=[
                vpc_id,
            ],
        ).get("Vpcs")

        if len(response) > 1:
            raise TestException("More than one vpc found!")

        if len(response) == 1:
            return response[0]
        elif len(response) == 0:
            return None

    def describe_vpcs(self, name: str):
        return self.ec2.describe_vpcs(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        name,
                    ],
                },
            ]
        ).get("Vpcs")

    def create_subnet(self, name: str, az, cidr: str, vpc_id: str):
        subnet_id = (
            self.ec2.create_subnet(
                TagSpecifications=[
                    {
                        "ResourceType": "subnet",
                        "Tags": [
                            {"Key": "Name", "Value": name},
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

        return subnet_id

    def describe_subnet(self, subnet_id: str):
        response = self.ec2.describe_subnets(
            SubnetIds=[
                subnet_id,
            ],
        ).get("Subnets")

        if len(response) > 1:
            raise TestException("More than one subnet found!")

        if len(response) == 1:
            return response[0]
        elif len(response) == 0:
            return None

    def describe_subnets(self, name: str):
        return self.ec2.describe_subnets(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        name,
                    ],
                },
            ]
        ).get("Subnets")

    def create_route_table(self, name: str, vpc_id: str):
        route_table_id = (
            self.ec2.create_route_table(
                TagSpecifications=[
                    {
                        "ResourceType": "route-table",
                        "Tags": [
                            {"Key": "Name", "Value": name},
                        ],
                    }
                ],
                VpcId=vpc_id,
            )
            .get("RouteTable")
            .get("RouteTableId")
        )

        return route_table_id

    def describe_route_table(self, route_table_id: str):
        response = self.ec2.describe_route_tables(
            RouteTableIds=[
                route_table_id,
            ],
        ).get("RouteTables")

        if len(response) > 1:
            raise TestException("More than one route table found!")

        if len(response) == 1:
            return response[0]
        elif len(response) == 0:
            return None

    def describe_route_tables(self, name: str):
        return self.ec2.describe_route_tables(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        name,
                    ],
                },
            ]
        ).get("RouteTables")

    def create_route(
        self, route_table_id: str, gate_id: str, destination_cidr: str
    ):
        self.ec2.create_route(
            DestinationCidrBlock=destination_cidr,
            GatewayId=gate_id,
            RouteTableId=route_table_id,
        )

    def describe_routes(self, route_table_id):
        return (
            self.ec2.describe_route_tables(
                RouteTableIds=[
                    route_table_id,
                ],
            )
            .get("RouteTables")[0]
            .get("Routes")
        )

    def associate_gateway_to_route_table(self, route_table_id, gate_id):
        self.ec2.associate_route_table(
            RouteTableId=route_table_id, GatewayId=gate_id
        )

    def associate_subnet_to_route_table(self, route_table_id, subnet_id):
        self.ec2.associate_route_table(
            RouteTableId=route_table_id, SubnetId=subnet_id
        )

    def create_internet_gateway(self, name: str):
        gate_id = (
            self.ec2.create_internet_gateway(
                TagSpecifications=[
                    {
                        "ResourceType": "internet-gateway",
                        "Tags": [
                            {"Key": "Name", "Value": name},
                        ],
                    }
                ]
            )
            .get("InternetGateway")
            .get("InternetGatewayId")
        )

        return gate_id

    def describe_internet_gateway(self, gate_id: str):
        response = self.ec2.describe_internet_gateways(
            InternetGatewayIds=[
                gate_id,
            ],
        ).get("InternetGateways")

        if len(response) > 1:
            raise TestException("More than one Internet gateway found!")

        if len(response) == 1:
            return response[0]
        elif len(response) == 0:
            return None

    def describe_internet_gateways(self, name: str):
        return self.ec2.describe_internet_gateways(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        name,
                    ],
                },
            ]
        ).get("InternetGateways")

    def attach_gateway_to_vpc(self, vpc_id, gate_id):
        self.ec2.attach_internet_gateway(
            InternetGatewayId=gate_id, VpcId=vpc_id
        )

    def create_security_group(self, name: str, description, vpc_id):
        return self.ec2.create_security_group(
            TagSpecifications=[
                {
                    "ResourceType": "security-group",
                    "Tags": [
                        {"Key": "Name", "Value": name},
                    ],
                }
            ],
            Description=description,
            GroupName=name,
            VpcId=vpc_id,
        ).get("GroupId")

    def describe_security_group(self, security_group_id: str):
        response = self.ec2.describe_security_groups(
            GroupIds=[
                security_group_id,
            ],
        ).get("SecurityGroups")

        if len(response) > 1:
            raise TestException("More than one security group found!")

        if len(response) == 1:
            return response[0]
        elif len(response) == 0:
            return None

    def describe_security_groups(self, name: str):
        return self.ec2.describe_security_groups(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        name,
                    ],
                },
            ]
        ).get("SecurityGroups")

    def allow_access_from_cidr(
        self,
        security_group_id: str,
        from_port: int,
        to_port: int,
        protocol: str,
        source_cidr: str,
        description: str,
    ):
        self.ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "FromPort": from_port,
                    "IpProtocol": protocol,
                    "IpRanges": [
                        {
                            "CidrIp": source_cidr,
                            "Description": description,
                        },
                    ],
                    "ToPort": to_port,
                },
            ],
        )

    def allow_access_from_security_group(
        self,
        security_group_id: str,
        from_port: int,
        to_port: int,
        protocol: str,
        source_security_group_id: str,
        description: str,
    ):
        self.ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "FromPort": from_port,
                    "IpProtocol": protocol,
                    "UserIdGroupPairs": [
                        {
                            "Description": description,
                            "GroupId": source_security_group_id,
                        },
                    ],
                    "ToPort": to_port,
                },
            ],
        )

    def create_instance(self, name, image_id):
        return (
            self.ec2.run_instances(
                ImageId=image_id,
                MinCount=1,
                MaxCount=1,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": name},
                        ],
                    }
                ],
            )
            .get("Instances")[0]
            .get("InstanceId")
        )

    def describe_instances(self, name: str):
        response = self.ec2.describe_instances(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        name,
                    ],
                },
            ],
        ).get("Reservations")

        if len(response) > 1:
            raise TestException("More than one reservation found!")

        if len(response) == 0:
            return response

        return response[0].get("Instances")

    def decribe_instance(self, instance_id: str):
        response = self.ec2.describe_instances(
            InstanceIds=[
                instance_id,
            ],
        ).get("Reservations")

        if len(response) > 1:
            raise TestException("More than one reservation found!")

        if len(response) == 0:
            return None

        instances = response[0].get("Instances")

        if len(instances) > 1:
            raise TestException("More than one instance found!")

        if len(instances) == 1:
            return instances[0]
        elif len(instances) == 0:
            return None

    def create_image(self, name: str, description: str, instance_id: str):
        return self.ec2.create_image(
            InstanceId=instance_id,
            Description=description,
            Name=name,
            TagSpecifications=[
                {
                    "ResourceType": "image",
                    "Tags": [
                        {"Key": "Name", "Value": name},
                    ],
                }
            ],
        ).get("ImageId")

    def describe_images(self, name: str):
        return self.ec2.describe_images(
            Filters=[
                {
                    "Name": "name",
                    "Values": [
                        name,
                    ],
                },
            ],
        ).get("Images")

    def decribe_image(self, image_id: str):
        response = self.ec2.describe_images(
            ImageIds=[
                image_id,
            ],
        ).get("Images")

        if len(response) > 1:
            raise TestException("More than one image found!")

        if len(response) == 1:
            return response[0]
        elif len(response) == 0:
            return None

    def decribe_snapshot(self, snapshot_id: str):
        response = self.ec2.describe_snapshots(
            SnapshotIds=[
                snapshot_id,
            ],
        ).get("Snapshots")

        if len(response) > 1:
            raise TestException("More than one snapshot found!")

        if len(response) == 1:
            return response[0]
        elif len(response) == 0:
            return None

    def create_keypair(self, name: str):
        response = self.ec2.create_key_pair(
            KeyName=name,
            KeyType="rsa",
            KeyFormat="pem",
        )

        private_key = response.get("KeyMaterial")
        private_key_file = f"{ProjectDirectories.ACCESS_DIR}/{name}"
        private_key_file_handle = open(private_key_file, "w")
        private_key_file_handle.write(private_key)
        private_key_file_handle.close()

        # Setting the given file to be read by the owner.
        os.chmod(private_key_file, stat.S_IREAD)

        return response.get("KeyPairId")

    def decribe_keypairs(self, name: str):
        try:
            return self.ec2.describe_key_pairs(
                KeyNames=[
                    name,
                ],
                IncludePublicKey=True,
            ).get("KeyPairs")
        except ClientError:
            return []

    def create_hosted_zone(self, name: str):
        return (
            self.route53.create_hosted_zone(
                Name=name, CallerReference=str(hash("maxmin"))
            )
            .get("HostedZone")
            .get("Id")
        )

    def describe_hosted_zones(self, name: str):
        return self.route53.list_hosted_zones_by_name(DNSName=name).get(
            "HostedZones"
        )

    def create_record(
        self, dns_name: str, ip_address: str, hosted_zone_id: str
    ):
        self.route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "CREATE",
                        "ResourceRecordSet": {
                            "Name": dns_name,
                            "Type": "A",
                            "TTL": 300,
                            "ResourceRecords": [{"Value": ip_address}],
                        },
                    }
                ]
            },
        )

    def describe_records(self, dns_name: str, hosted_zone_id: str):
        return self.route53.list_resource_record_sets(
            HostedZoneId=hosted_zone_id, StartRecordName=dns_name
        ).get("ResourceRecordSets")
