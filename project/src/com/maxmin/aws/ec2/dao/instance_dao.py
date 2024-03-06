"""
Created on Mar 26, 2023

@author: vagrant
"""
from com.maxmin.aws.client import Ec2Dao
from com.maxmin.aws.constants import Ec2Constants
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger
from com.maxmin.aws.ec2.domain.tag import Tag
import json

class InstanceDao(Ec2Dao):
    """
    classdocs
    """

    def __init__(self, name: str):
        super().__init__()

        self.id = None
        self.name = name
        self.state = None
        self.az = None
        self.private_ip = None
        self.public_ip = None
        self.instance_profile = None
        self.security_group_id = None
        self.subnet_id = None
        self.image_id = None
        self.vpc_id = None
        self.tags = []
        self.dns_domain = None

    def load(self) -> bool:
        """
        Loads the instance data, throws an error if more than 1 is found with the same Tag Name,
        returns True if an instance is found, False otherwise.
        """
        
        response = self.ec2.describe_instances(
            Filters=[
                {
                    "Name": "tag-value",
                    "Values": [self.name],
                },
            ],
        ).get("Reservations")

        if len(response) > 1:
            raise AwsException("Found more than 1 reservation!")
        elif len(response) == 0:
            return False

        instances = response[0].get("Instances")

        if len(instances) > 1:
            # do not allow more instance with the same tag Name.
            raise AwsException("Found more than 1 instance with the same name!")

        if len(instances) == 0:
            return False
        else:
            self.id = instances[0].get("InstanceId")
            self.state = instances[0].get("State").get("Name")
            self.az = instances[0].get("Placement").get("AvailabilityZone")
            self.private_ip = instances[0].get("PrivateIpAddress")
            self.public_ip = instances[0].get("PublicIpAddress")
            self.instance_profile = instances[0].get("IamInstanceProfile")
            self.security_group_id = (
                instances[0].get("Placement").get("GroupId")
            )
            self.subnet_id = instances[0].get("SubnetId")
            self.vpc_id = instances[0].get("VpcId")
            self.image_id = instances[0].get("ImageId")
            
            for tag in instances[0].get("Tags"):
                tag = Tag(tag.get("Key"), tag.get("Value"))
                self.tags.append(tag)

            return True

    def create(
        self,
        image_id: str,
        security_group_id: str,
        subnet_id: str,
        private_ip: str,
        user_data_b64: str,
        tags: list,
    ) -> None:
        """
        Creates/runs an instance and waits until it's available.
        The instance is assigned a public IP address, not a static/elastic one.

        tags: a list of {"Key": xxxx, "Value": yyyy} objects
        """

        if self.load() is True:
            # do not allow more than one instance with the same name.
            raise AwsException("Instance already created!")

        ec2_constants = Ec2Constants()
        tag_specifications = [{
                                "ResourceType": "instance", 
                                "Tags": []
                            }]
        
        for tag_config in tags:
            tag_specifications[0]['Tags'].append(tag_config.to_dictionary())

        try:
            self.id = (
                self.ec2.run_instances(
                    BlockDeviceMappings=[
                        {
                            "DeviceName": ec2_constants.device,
                            "Ebs": {
                                "VolumeSize": ec2_constants.volume_size,
                            },
                        },
                    ],
                    ImageId=image_id,
                    InstanceType=ec2_constants.instance_type,
                    MaxCount=1,
                    MinCount=1,
                    Placement={
                        "Tenancy": ec2_constants.tenancy,
                    },
                    UserData=user_data_b64,
                    NetworkInterfaces=[
                        {
                            "DeviceIndex": 0,
                            "SubnetId": subnet_id,
                            "Groups": [security_group_id],
                            "PrivateIpAddress": private_ip,
                            "AssociatePublicIpAddress": True,
                        },
                    ],
                    TagSpecifications=tag_specifications,
                )
                .get("Instances")[0]
                .get("InstanceId")
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the instance!")

        waiter = self.ec2.get_waiter("instance_status_ok")
        waiter.wait(InstanceIds=[self.id])

    def delete(self) -> None:
        """
        Terminates the instance and waits until successful.
        Terminated instances remain visible after termination (for approximately
        one hour).
        By default, Amazon EC2 deletes all EBS volumes that were attached when
        the instance launched. Volumes attached after instance launch continue
        running.
        """

        try:
            self.ec2.terminate_instances(
                InstanceIds=[
                    self.id,
                ],
            )
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the instance!")

        waiter = self.ec2.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=[self.id])
