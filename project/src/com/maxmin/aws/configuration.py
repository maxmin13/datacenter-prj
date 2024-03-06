"""
Created on Mar 13, 2023

@author: vagrant
"""
import json
from json.decoder import JSONDecodeError
from pathlib import Path

from com.maxmin.aws.exception import AwsException


class HostedZoneConfig(object):
    """
    Loads a JSON file into a configuration object.
    """

    def __init__(self, config_file):
        self.description = None
        self.registered_domain = None

        try:
            config_file_path = Path(config_file)
            content = config_file_path.read_text("UTF8")
        except FileNotFoundError:
            raise AwsException("Error reading configuration file!")

        try:
            self._hosted_zone = json.loads(content).get("HostedZone")
        except JSONDecodeError:
            raise AwsException("Invalid JSON file!")

        self.description = self._hosted_zone.get("Description")
        self.registered_domain = self._hosted_zone.get("RegisteredDomain")


class DatacenterConfig(object):
    """
    Loads a JSON file into a configuration object.
    """

    def __init__(self, config_file):
        self.vpc = None
        self.subnets = []
        self.internet_gateway = None
        self.security_groups = []
        self.instances = []

        try:
            config_file_path = Path(config_file)
            content = config_file_path.read_text("UTF8")
        except FileNotFoundError:
            raise AwsException("Error reading configuration file!")

        try:
            self._datacenter = json.loads(content).get("Datacenter")
        except JSONDecodeError:
            raise AwsException("Invalid JSON file!")

        self.vpc = VpcConfig(
            self._datacenter.get("Name"),
            self._datacenter.get("Description"),
            self._datacenter.get("Cidr"),
            self._datacenter.get("Gateway"),
            self._datacenter.get("Region"),
            self._datacenter.get("RouteTable"),
        )

        for subnet in self._datacenter.get("Subnets"):
            self.subnets.append(
                SubnetConfig(
                    subnet.get("Name"),
                    subnet.get("Description"),
                    subnet.get("Az"),
                    subnet.get("Cidr"),
                )
            )

        self.internet_gateway = self._datacenter.get("InternetGateway")
        self.route_table = self._datacenter.get("RouteTable")

        for security_group in self._datacenter.get("SecurityGroups"):
            group_config = SecurityGroupConfig(
                security_group.get("Name"),
                security_group.get("Description"),
            )

            self.security_groups.append(group_config)

            rules = security_group.get("Rules")

            for rule in rules:
                if "SgpId" in rule:
                    rule_config = SgpRuleConfig(
                        rule.get("FromPort"),
                        rule.get("ToPort"),
                        rule.get("Protocol"),
                        rule.get("SgpId"),
                        rule.get("Description"),
                    )
                else:
                    rule_config = CidrRuleConfig(
                        rule.get("FromPort"),
                        rule.get("ToPort"),
                        rule.get("Protocol"),
                        rule.get("Cidr"),
                        rule.get("Description"),
                    )

                group_config.rules.append(rule_config)

        for instance in self._datacenter.get("Instances"):
            
            instance_config = InstanceConfig(
                    instance.get("UserName"),
                    instance.get("UserPassword"),
                    instance.get("PrivateIp"),
                    instance.get("SecurityGroup"),
                    instance.get("Subnet"),
                    instance.get("ParentImage"),
                    instance.get("TargetImage"),
                    instance.get("DnsDomain"),
                    instance.get("HostName"),
                )
            
            for tag in instance.get("Tags"):
                tag_config = TagConfig(tag.get("Key"), tag.get("Value"))
                instance_config.tags.append(tag_config)
            
            self.instances.append(
                instance_config
            )


class VpcConfig(object):
    def __init__(
        self,
        name,
        description,
        cidr,
        gateway,
        region,
        route_table,
    ):
        self.name = name
        self.description = description
        self.cidr = cidr
        self.gateway = gateway
        self.region = region
        self.route_table = route_table


class SubnetConfig(object):
    def __init__(self, name, description, az, cidr):
        self.name = name
        self.description = description
        self.az = az
        self.cidr = cidr


class InternetGatewayConfig(object):
    def __init__(self, name):
        self.name = name


class RouteTableConfig(object):
    def __init__(self, name):
        self.name = name


class SecurityGroupConfig(object):
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.rules = []


class CidrRuleConfig(object):
    def __init__(self, from_port, to_port, protocol, cidr, description):
        self.from_port = from_port
        self.to_port = to_port
        self.protocol = protocol
        self.cidr = cidr
        self.description = description


class SgpRuleConfig(object):
    def __init__(self, from_port, to_port, protocol, sgp_id, description):
        self.from_port = from_port
        self.to_port = to_port
        self.protocol = protocol
        self.sgp_id = sgp_id
        self.description = description


class InstanceConfig(object):
    def __init__(
        self,
        username,
        password,
        private_ip,
        security_group,
        subnet,
        parent_img,
        target_img,
        dns_domain,
        host_name,
    ):
        self.username = username
        self.password = password
        self.private_ip = private_ip
        self.security_group = security_group
        self.subnet = subnet
        self.parent_img = parent_img
        self.target_img = target_img
        self.tags = []
        self.dns_domain = dns_domain
        self.host_name = host_name

class TagConfig(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value
        
    def to_dictionary(self)->str:
        
        dictionary = self.__dict__
        new_dict = dict()
        
        for key, value in dictionary.items():
            new_dict[str.capitalize(key)] = value 

        return new_dict
    