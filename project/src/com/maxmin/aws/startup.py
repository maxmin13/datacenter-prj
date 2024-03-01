import sys

from com.maxmin.aws.configuration import (
    DatacenterConfig,
    CidrRuleConfig,
    HostedZoneConfig,
)
from com.maxmin.aws.ec2.dao import internet_gateway, instance
from com.maxmin.aws.ec2.dao.instance import Instance
from com.maxmin.aws.ec2.dao.internet_gateway import InternetGateway
from com.maxmin.aws.ec2.dao.route_table import RouteTable
from com.maxmin.aws.ec2.dao.security_group import (
    SecurityGroup,
    CidrRule,
    SgpRule,
)
from com.maxmin.aws.ec2.dao.ssh import Keypair
from com.maxmin.aws.ec2.dao.subnet import Subnet
from com.maxmin.aws.ec2.dao.vpc import Vpc
from com.maxmin.aws.ec2.service.instance import InstanceService
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.route53.service.hosted_zone import HostedZoneService
from com.maxmin.aws.constants import ProjectDirectories

if __name__ == "__main__":
    # datacenter.json
    datacenter_config = DatacenterConfig(sys.argv[1])

    # hostedzone.json
    hostedzone_config = HostedZoneConfig(sys.argv[2])

    Logger.info("Creating datacenter ...")

    #
    # Create the vpc
    #

    vpc = Vpc(datacenter_config.vpc.name)

    if vpc.load() is False:
        vpc.create(datacenter_config.vpc.cidr)

        Logger.info("Vpc created!")
    else:
        Logger.warn("Vpc already created!")

    vpc.load()

    #
    # Create the Internet gateway
    #

    internet_gateway = InternetGateway(datacenter_config.internet_gateway)

    if internet_gateway.load() is False:
        internet_gateway.create()

        Logger.info("Internet gateway created!")
    else:
        Logger.warn("Internet gateway already created!")

    internet_gateway.load()

    if internet_gateway.is_attached_to(vpc.id) is False:
        internet_gateway.attach_to(vpc.id)

        Logger.info("Internet gateway attached to the vpc!")
    else:
        Logger.warn("The internet gateway is already attached to the vpc!")

    #
    # Create the route table
    #

    route_table = RouteTable(datacenter_config.route_table)

    if route_table.load() is False:
        route_table.create(vpc.id)

        Logger.info("Route table created!")
    else:
        Logger.warn("Route table already created!")

    route_table.load()

    if route_table.has_route(internet_gateway.id, "0.0.0.0/0") is False:
        route_table.create_route(internet_gateway.id, "0.0.0.0/0")

        Logger.info("Route to the Internet gateway created!")
    else:
        Logger.warn("Route to the Internet gateway already created!")

    #
    # Create the subnet
    #

    for subnet_config in datacenter_config.subnets:
        subnet = Subnet(subnet_config.name)

        if subnet.load() is False:
            subnet.create(subnet_config.az, subnet_config.cidr, vpc.id)

            Logger.info("Subnet created!")
        else:
            Logger.warn("Subnet already created!")

        route_table.associate_subnet(subnet.id)

    #
    # Create the security group
    #

    for security_group_config in datacenter_config.security_groups:
        security_group = SecurityGroup(security_group_config.name)

        if security_group.load() is False:
            security_group.create(security_group_config.description, vpc.id)
            security_group.load()

            Logger.info("Security group created!")

            rules_config = security_group_config.rules

            for rule_config in rules_config:
                if isinstance(rule_config, CidrRuleConfig):
                    cidr_rule = CidrRule(security_group.id)

                    if (
                        cidr_rule.load(
                            rule_config.from_port,
                            rule_config.to_port,
                            rule_config.protocol,
                            rule_config.cidr,
                            rule_config.description,
                        )
                        is False
                    ):
                        cidr_rule.create(
                            rule_config.from_port,
                            rule_config.to_port,
                            rule_config.protocol,
                            rule_config.cidr,
                            rule_config.description,
                        )

                        Logger.info("Cidr rule created!")
                    else:
                        Logger.warn("Cidr rule already created!")
                else:
                    sgp_rule = SgpRule(security_group.id)

                    if (
                        sgp_rule.load(
                            rule_config.from_port,
                            rule_config.to_port,
                            rule_config.protocol,
                            rule_config.sgp_id,
                            rule_config.description,
                        )
                        is False
                    ):
                        sgp_rule.create(
                            rule_config.from_port,
                            rule_config.to_port,
                            rule_config.protocol,
                            rule_config.cidr,
                            rule_config.description,
                        )

                        Logger.info("Sgp rule created!")
                    else:
                        Logger.warn("Sgp rule already created!")
        else:
            Logger.warn("Security group already created!")

    #
    # Create the instances and AMIs.
    #

    for instance_config in datacenter_config.instances:
        for tag in instance_config.tags:
            if tag.get("Key") == "Name":
                key_name = tag.get("Value")
                keypair = Keypair(key_name, ProjectDirectories.ACCESS_DIR)
                break

        if not key_name:
            raise AwsException("SSH key name not found in configuration.")

        if keypair.load() is False:
            keypair.create()

            Logger.info("Keypair created!")

            keypair.load()
        else:
            Logger.warn("Keypair already created!")

        instance = Instance(instance_config.tags)
        instance.load()

        if instance.state == "terminated":
            raise AwsException(
                "The instance is terminated, you may need to wait a while, or change the instance name in datacenter.json file."
            )

        instance_service = InstanceService()
        instance_service.create_instance(
            instance_config.parent_img,
            instance_config.security_group,
            instance_config.subnet,
            keypair,
            instance_config.private_ip,
            instance_config.username,
            instance_config.password,
            instance_config.tags,
            instance_config.host_name,
        )

        instance.load()

        Logger.info("Creating DNS record ...")

        hosted_zone_service = HostedZoneService()

        if (
            hosted_zone_service.check_record_exists(
                hostedzone_config.registered_domain,
                instance_config.dns_name,
                instance.public_ip,
            )
            is False
        ):
            hosted_zone_service.create_record(
                hostedzone_config.registered_domain,
                instance_config.dns_name,
                instance.public_ip,
            )

            Logger.info("DNS record created!")
        else:
            Logger.warn("DNS record already created!")

    Logger.info("Datacenter created!")
    Logger.info(instance_config.dns_name)
    Logger.info(instance.public_ip)
