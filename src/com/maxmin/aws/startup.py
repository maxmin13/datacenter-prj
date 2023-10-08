import sys

from com.maxmin.aws.configuration import ApplicationConfig, CidrRuleConfig
from com.maxmin.aws.constants import ProjectFiles, Route53Constants
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
from com.maxmin.aws.route53.dao.hosted_zone import HostedZone
from com.maxmin.aws.route53.dao.record import Record


if __name__ == "__main__":
    if len(sys.argv) < 2:
        application_config = ApplicationConfig(
            ProjectFiles.DEFAULT_CONFIG_FILE
        )
    else:
        application_config = ApplicationConfig(sys.argv[1])

    Logger.info("Creating datacenter ...")

    #
    # Create the vpc
    #

    vpc = Vpc(application_config.vpc.name)

    if vpc.load() is False:
        vpc.create(application_config.vpc.cidr)

        Logger.info("Vpc created!")
    else:
        Logger.warn("Vpc already created!")

    vpc.load()

    #
    # Create the Internet gateway
    #

    internet_gateway = InternetGateway(application_config.internet_gateway)

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

    route_table = RouteTable(application_config.route_table)

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

    for subnet_config in application_config.subnets:
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

    for security_group_config in application_config.security_groups:
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

    for instance_config in application_config.instances:
        keypair = Keypair(instance_config.keypair)

        if keypair.load() is False:
            keypair.create()

            Logger.info("Keypair created!")

            keypair.load()
        else:
            Logger.warn("Keypair already created!")

        instance = Instance(instance_config.tags)
        instance.load()

        if instance.state == "terminated":
            raise AwsException("The instance is terminated.")

        instance_service = InstanceService()
        instance_service.create_instance(
            instance_config.parent_img,
            instance_config.security_group,
            instance_config.subnet,
            instance_config.keypair,
            instance_config.private_ip,
            instance_config.hostname,
            instance_config.username,
            instance_config.password,
            instance_config.tags,
        )

        instance.load()

        route53Constants = Route53Constants()
        hosted_zone = HostedZone(route53Constants.registered_domain)
        hosted_zone.load()
        record = Record(instance_config.dns_name, hosted_zone.id)

        Logger.info("Creating DNS record ...")

        if record.load() is False:
            record.create(instance.public_ip)

            Logger.info("DNS record created!")
        else:
            Logger.warn("DNS record already created!")

        # TODO TODO
        # persist the instance into an AMI
        # if instance_config.target_img is not None:
        #    target_image = Image(instance_config.target_img)

        #    if target_image.load() is False:
        #        Logger.info("Creating target image ...")

        #       instance.stop()
        #        target_image.create(instance.id, target_image.name)

        #        Logger.info("Target image created!")
        #    else:
        #        Logger.warn("Target image not found!")

    Logger.info("Datacenter created!")
