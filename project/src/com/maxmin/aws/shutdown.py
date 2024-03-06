import sys

from com.maxmin.aws.configuration import DatacenterConfig, HostedZoneConfig
from com.maxmin.aws.ec2.dao.image_dao import ImageDao
from com.maxmin.aws.ec2.dao.instance_dao import InstanceDao
from com.maxmin.aws.ec2.dao.internet_gateway_dao import InternetGatewayDao
from com.maxmin.aws.ec2.dao.route_table_dao import RouteTableDao
from com.maxmin.aws.ec2.dao.security_group_dao import SecurityGroupDao
from com.maxmin.aws.ec2.dao.ssh_dao import KeypairDao
from com.maxmin.aws.ec2.dao.subnet_dao import SubnetDao
from com.maxmin.aws.ec2.dao.vpc_dao import VpcDao
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.constants import ProjectDirectories
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.route53.dao.hosted_zone_dao import HostedZoneDao
from com.maxmin.aws.route53.dao.record_dao import RecordDao

if __name__ == "__main__":
    datacenter_config = DatacenterConfig(sys.argv[1])
    hostedzone_config = HostedZoneConfig(sys.argv[2])

    Logger.info("Deleting data center ...")

    vpc_dao = VpcDao(datacenter_config.vpc.name)

    if vpc_dao.load() is False:
        Logger.warn("VPC not found!")

    #
    # Delete the instances
    #

    for instance_config in datacenter_config.instances:
        
        for tag_config in instance_config.tags:
            if tag_config.key == "Name":
                instance_nm = tag_config.value
                break

        if not instance_nm:
            raise AwsException("Instance name not found in configuration.")
        
        instance_dao = InstanceDao(instance_nm)

        found_instance = instance_dao.load()

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
                        Logger.warn("DNS record already deleted!")
                    else:
                        record_dao = RecordDao(
                            instance_config.dns_domain, hosted_zone_dao.id
                        )
                        record_dao.delete(instance_dao.public_ip)

                        Logger.info("DNS record deleted!")

            except Exception as e:
                Logger.warn(str(e))

        if found_instance is True and instance_dao.state != "terminated":
            Logger.info("Deleting instance ...")

            instance_dao.delete()

            Logger.info("Instance deleted!")

        else:
            Logger.warn("Instance already deleted!")

        keypair_dao = KeypairDao(instance_nm, ProjectDirectories.ACCESS_DIR)
        if keypair_dao.load() is True:
            keypair_dao.delete()

        # delete the corresponding AMI
        if instance_config.target_img is not None:
            target_image_dao = ImageDao(instance_config.target_img)

            if target_image_dao.load() is True:
                Logger.info("Deleting target image ...")

                target_image_dao.delete()

                Logger.info("Target image deleted!")
            else:
                Logger.warn("Target image not found!")

    #
    # Delete the security groups
    #

    for security_group_config in datacenter_config.security_groups:
        security_group_dao= SecurityGroupDao(security_group_config.name)

        if security_group_dao.load() is True:
            security_group_dao.delete()

            Logger.info("Security group deleted!")
        else:
            Logger.warn("Security group already deleted!")

    #
    # Delete the internet gateway
    #

    internet_gateway_dao = InternetGatewayDao(datacenter_config.internet_gateway)

    if internet_gateway_dao.load() is True:
        if internet_gateway_dao.is_attached_to(vpc_dao.id):
            internet_gateway_dao.detach_from(vpc_dao.id)

        internet_gateway_dao.delete()

        Logger.info("Internet gateway deleted!")
    else:
        Logger.warn("Internet gateway already deleted!")

    #
    # Delete the subnets
    #

    for subnet_config in datacenter_config.subnets:
        subnet_dao = SubnetDao(subnet_config.name)

        if subnet_dao.load() is True:
            subnet_dao.delete()

            Logger.info("Subnet deleted!")
        else:
            Logger.warn("Subnet already deleted!")

    #
    # Delete the route table
    #

    route_table_dao = RouteTableDao(datacenter_config.route_table)

    if route_table_dao.load() is True:
        route_table_dao.delete()

        Logger.info("Route table deleted!")
    else:
        Logger.warn("Route table already deleted!")

    #
    # Delete the vpc
    #

    vpc_dao = VpcDao(datacenter_config.vpc.name)
    vpc_found = vpc_dao.load()

    if vpc_found is True:
        vpc_dao.delete()

        Logger.info("VPC delete!")
    else:
        Logger.warn("VPC already deleted!")

    Logger.info("Data center deleted!")
