import sys

from com.maxmin.aws.configuration import (
    DatacenterConfig,
    CidrRuleConfig,
    HostedZoneConfig,
)

from com.maxmin.aws.ec2.dao.instance_dao import InstanceDao
from com.maxmin.aws.ec2.dao.internet_gateway_dao import InternetGatewayDao
from com.maxmin.aws.ec2.dao.route_table_dao import RouteTableDao
from com.maxmin.aws.ec2.dao.ssh_dao import KeypairDao
from com.maxmin.aws.ec2.dao.subnet_dao import SubnetDao
from com.maxmin.aws.ec2.dao.vpc_dao import VpcDao
from com.maxmin.aws.ec2.service.instance_service import InstanceService
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.constants import ProjectDirectories
from com.maxmin.aws.route53.dao.hosted_zone_dao import HostedZoneDao
from com.maxmin.aws.route53.dao.record_dao import RecordDao
from com.maxmin.aws.ec2.dao.security_group_dao import SecurityGroupDao, CidrRuleDao, SgpRuleDao

if __name__ == "__main__":
    # datacenter.json
    datacenter_config = DatacenterConfig(sys.argv[1])

    # hostedzone.json
    hostedzone_config = HostedZoneConfig(sys.argv[2])

    Logger.info("Creating data center ...")

    #
    # Create the vpc
    #

    vpc_dao = VpcDao(datacenter_config.vpc.name)

    if vpc_dao.load() is False:
        vpc_dao.create(datacenter_config.vpc.cidr)

        Logger.info("VPC created!")
    else:
        Logger.warn("VPC already created!")

    #
    # Create the Internet gateway
    #

    internet_gateway_dao = InternetGatewayDao(datacenter_config.internet_gateway)

    if internet_gateway_dao.load() is False:
        internet_gateway_dao.create()

        Logger.info("Internet gateway created!")
    else:
        Logger.warn("Internet gateway already created!")

    if internet_gateway_dao.is_attached_to(vpc_dao.id) is False:
        internet_gateway_dao.attach_to(vpc_dao.id)

        Logger.info("Internet gateway attached to the vpc!")
    else:
        Logger.warn("The Internet gateway is already attached to the vpc!")

    #
    # Create the route table
    #

    route_table_dao = RouteTableDao(datacenter_config.route_table)

    if route_table_dao.load() is False:
        route_table_dao.create(vpc_dao.id)

        Logger.info("Route table created!")
    else:
        Logger.warn("Route table already created!")

    if route_table_dao.has_route(internet_gateway_dao.id, "0.0.0.0/0") is False:
        route_table_dao.create_route(internet_gateway_dao.id, "0.0.0.0/0")

        Logger.info("Route to the Internet gateway created!")
    else:
        Logger.warn("Route to the Internet gateway already created!")

    #
    # Create the subnet
    #

    for subnet_config in datacenter_config.subnets:
        subnet_dao = SubnetDao(subnet_config.name)

        if subnet_dao.load() is False:
            subnet_dao.create(subnet_config.az, subnet_config.cidr, vpc_dao.id)

            Logger.info("Subnet created!")
        else:
            Logger.warn("Subnet already created!")

        route_table_dao.associate_subnet(subnet_dao.id)

    #
    # Create the security group
    #

    for security_group_config in datacenter_config.security_groups:
        security_group_dao = SecurityGroupDao(security_group_config.name)

        if security_group_dao.load() is False:
            security_group_dao.create(security_group_config.description, vpc_dao.id)
            security_group_dao.load()

            Logger.info("Security group created!")

            rules_config = security_group_config.rules

            for rule_config in rules_config:
                if isinstance(rule_config, CidrRuleConfig):
                    cidr_rule_dao = CidrRuleDao(security_group_dao.id)

                    if (
                        cidr_rule_dao.load(
                            rule_config.from_port,
                            rule_config.to_port,
                            rule_config.protocol,
                            rule_config.cidr,
                            rule_config.description,
                        )
                        is False
                    ):
                        cidr_rule_dao.create(
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
                    sgp_rule_dao = SgpRuleDao(security_group_dao.id)

                    if (
                        sgp_rule_dao.load(
                            rule_config.from_port,
                            rule_config.to_port,
                            rule_config.protocol,
                            rule_config.sgp_id,
                            rule_config.description,
                        )
                        is False
                    ):
                        sgp_rule_dao.create(
                            rule_config.from_port,
                            rule_config.to_port,
                            rule_config.protocol,
                            rule_config.cidr,
                            rule_config.description,
                        )

                        Logger.info("Security Group rule created!")
                    else:
                        Logger.warn("Security Group rule already created!")
        else:
            Logger.warn("Security group already created!")

    #
    # Create the instances and AMIs.
    #

    for instance_config in datacenter_config.instances:
        for tag_config in instance_config.tags:
            if tag_config.key == "Name":
                instance_nm = tag_config.value
                break

        if not instance_nm:
            raise AwsException("Instance name not found in configuration.")
        
        keypair_dao = KeypairDao(instance_nm, ProjectDirectories.ACCESS_DIR)

        if keypair_dao.load() is False:
            keypair_dao.create()

            Logger.info("Key pair created!")

            keypair_dao.load()
        else:
            Logger.warn("Key pair already created!")

        instance_dao = InstanceDao(instance_nm)
        instance_dao.load()

        if instance_dao.state == "terminated":
            raise AwsException(
                "The instance_dao is terminated, you may need to wait a while, or change the instance_dao name in datacenter.json file."
            )

        instance_service = InstanceService()
        instance_service.create_instance(
            instance_nm,
            instance_config.parent_img,
            instance_config.security_group,
            instance_config.subnet,
            keypair_dao,
            instance_config.private_ip,
            instance_config.username,
            instance_config.password,
            instance_config.tags,
            instance_config.host_name,
        )
        
        instance_dao.load() 

        if (
            not hostedzone_config.registered_domain
            or not instance_config.dns_domain
        ):
            Logger.warn("Incomplete DNS data configuration!")
        else:
            try:
                hosted_zone_dao = HostedZoneDao(hostedzone_config.registered_domain)
                if hosted_zone_dao.load() is False:
                    Logger.warn("DNS Hosted zone doesn't exist!")
                else:
                    record_dao = RecordDao(instance_config.dns_domain, hosted_zone_dao.id)
                    if record_dao.load() is False:
                        Logger.info("DNS record doesn't exists, creating ...")

                        record_dao.create(instance_dao.public_ip)

                        Logger.info("DNS record created!")
                    else:
                        Logger.warn("DNS record already created!")

            except Exception as e:
                Logger.warn(str(e))
                
    Logger.info("Data center created!")

    if instance_config.dns_domain:
        Logger.info("Instance DNS name: " + instance_config.dns_domain)

    Logger.info("Instance IP address: " + instance_dao.public_ip)
