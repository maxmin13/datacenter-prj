"""
Created on Mar 24, 2023

@author: vagrant
"""
from abc import abstractmethod

from botocore.exceptions import ClientError

from com.maxmin.aws.client import Ec2
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class SecurityGroup(Ec2):
    """
    Class that represents an AWS security group.
    """

    def __init__(self, name: str):
        """
        Constructor
        """
        super().__init__()
        self.name = name
        self.description = None
        self.id = None
        self.vpc_id = None

    def load(self) -> bool:
        """
        Loads the security group data, throws an error if more than 1 group
        are found, returns True if one is found, False otherwise.
        """

        response = self.ec2.describe_security_groups(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [
                        self.name,
                    ],
                },
            ],
        ).get("SecurityGroups")

        if len(response) > 1:
            raise AwsException("Found more than 1 security group!")

        if len(response) == 0:
            return False
        else:
            self.id = response[0].get("GroupId")
            self.vpc_id = response[0].get("VpcId")
            self.description = response[0].get("Description")

            return True

    def create(self, description: str, vpc_id: str) -> None:
        """
        Creates a security group and waits until it exists.
        """

        if self.load() is True:
            raise AwsException("Security group already created!")

        try:
            self.id = self.ec2.create_security_group(
                TagSpecifications=[
                    {
                        "ResourceType": "security-group",
                        "Tags": [
                            {"Key": "Name", "Value": self.name},
                        ],
                    }
                ],
                Description=description,
                GroupName=self.name,
                VpcId=vpc_id,
            ).get("GroupId")
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the security group!")

        waiter = self.ec2.get_waiter("security_group_exists")
        waiter.wait(GroupIds=[self.id])

    def delete(self) -> None:
        """
        Deletes the security group.
        """
        try:
            self.ec2.delete_security_group(GroupId=self.id)
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the security group!")


class AbstractRule(Ec2):
    def __init__(self, security_group_id: str):
        """
        Constructor
        """
        super().__init__()
        self.security_group_id = security_group_id

    @abstractmethod
    def load(self, from_port: str, to_port: str, protocol: str) -> bool:
        """
        Loads a rule by security group id, filtering by ports and protocol.
        """
        rules = []

        try:
            rules = (
                self.ec2.describe_security_groups(
                    GroupIds=[
                        self.security_group_id,
                    ],
                )
                .get("SecurityGroups")[0]
                .get("IpPermissions")
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidGroup.NotFound":
                Logger.warn(str(e))
                return rules
            else:
                Logger.error(str(e))
                raise AwsException("Error creating the security rule!")

        rules = list(
            filter(lambda rule: rule.get("FromPort") == from_port, rules)
        )

        rules = list(filter(lambda rule: rule.get("ToPort") == to_port, rules))

        rules = list(
            filter(lambda rule: rule.get("IpProtocol") == protocol, rules)
        )

        return rules


class CidrRule(AbstractRule):
    """
    Class that represents an AWS security group rule based on CIDR.
    """

    def __init__(self, security_group_id: str):
        """
        Constructor
        """
        super().__init__(security_group_id)
        self.from_port = None
        self.to_port = None
        self.protocol = None
        self.source_cidr = None
        self.description = None

    def load(
        self,
        from_port: str,
        to_port: str,
        protocol: str,
        source_cidr: str,
        description: str,
    ) -> bool:
        """
        Loads a rule.
        """
        rules = super().load(from_port, to_port, protocol)

        if len(rules) == 0:
            return False

        rule = rules[0]

        ip_ranges = rule.get("IpRanges")

        ip_ranges = list(
            filter(
                lambda ip_range: ip_range.get("CidrIp") == source_cidr,
                ip_ranges,
            )
        )

        ip_ranges = list(
            filter(
                lambda ip_range: ip_range.get("Description") == description,
                ip_ranges,
            )
        )

        if len(ip_ranges) == 0:
            return False
        else:
            ip_range = ip_ranges[0]

            self.from_port = rule.get("FromPort")
            self.to_port = rule.get("ToPort")
            self.protocol = rule.get("IpProtocol")
            self.description = ip_range.get("Description")
            self.source_cidr = ip_range.get("CidrIp")

            return True

    def create(
        self,
        from_port: int,
        to_port: int,
        protocol: str,
        source_cidr: str,
        description: str,
    ):
        """
        Adds an inbound (ingress) rule to a security group.
        """
        try:
            self.ec2.authorize_security_group_ingress(
                GroupId=self.security_group_id,
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
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error allowing access from cidr!")

    def delete(
        self,
        from_port: int,
        to_port: int,
        protocol: str,
        source_cidr: str,
        description: str,
    ):
        """
        Removes the specified inbound (ingress) rules from a security group.
        """
        try:
            self.ec2.revoke_security_group_ingress(
                GroupId=self.security_group_id,
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
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error revoking access from cidr!")


class SgpRule(AbstractRule):
    """
    Class that represents an AWS security group rule based on security group id.
    """

    def __init__(self, security_group_id: str):
        """
        Constructor
        """
        super().__init__(security_group_id)
        self.description = None
        self.from_port = None
        self.to_port = None
        self.protocol = None
        self.source_security_group_id = None

    def load(
        self,
        from_port: str,
        to_port: str,
        protocol: str,
        source_security_group_id: str,
        description: str,
    ) -> bool:
        """
        Loads a rule.
        """
        rules = super().load(from_port, to_port, protocol)

        if len(rules) == 0:
            return False

        rule = rules[0]

        groups = rule.get("UserIdGroupPairs")

        groups = list(
            filter(
                lambda group: group.get("GroupId") == source_security_group_id,
                groups,
            )
        )

        groups = list(
            filter(
                lambda group: group.get("Description") == description, groups
            )
        )

        if len(groups) == 0:
            return False
        else:
            group = groups[0]

            self.from_port = rule.get("FromPort")
            self.to_port = rule.get("ToPort")
            self.protocol = rule.get("IpProtocol")
            self.description = group.get("Description")
            self.source_security_group_id = group.get("GroupId")

            return True

    def create(
        self,
        from_port: int,
        to_port: int,
        protocol: str,
        source_security_group_id: str,
        description: str,
    ):
        """
        Adds an inbound (ingress) rules to a security group.
        Enables inbound traffic on a specified port from the specified security
        group.
        The group must be in the same VPC or a peer VPC.
        Incoming traffic is allowed based on the private IP addresses of
        instances that are associated with the specified security group.
        """
        try:
            self.ec2.authorize_security_group_ingress(
                GroupId=self.security_group_id,
                IpPermissions=[
                    {
                        "FromPort": from_port,
                        "IpProtocol": protocol,
                        "UserIdGroupPairs": [
                            {
                                "GroupId": source_security_group_id,
                                "Description": description,
                            },
                        ],
                        "ToPort": to_port,
                    },
                ],
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error allowing access from security group!")

    def delete(
        self,
        from_port: int,
        to_port: int,
        protocol: str,
        source_security_group_id: str,
        description: str,
    ):
        """
        Removes the specified inbound (ingress) rules from a security group.
        """
        try:
            self.ec2.revoke_security_group_ingress(
                GroupId=self.security_group_id,
                IpPermissions=[
                    {
                        "FromPort": from_port,
                        "IpProtocol": protocol,
                        "UserIdGroupPairs": [
                            {
                                "GroupId": source_security_group_id,
                                "Description": description,
                            },
                        ],
                        "ToPort": to_port,
                    },
                ],
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error revoking access from security group!")
