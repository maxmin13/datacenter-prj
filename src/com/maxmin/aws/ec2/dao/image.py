"""
Created on Mar 27, 2023

@author: vagrant
"""
from com.maxmin.aws.client import Ec2
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class Image(Ec2):
    """
    Describes an image (AMI) available in AWS.
    """

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.id = None
        self.state = None
        self.description = None
        self.snapshot_ids = []

    def load(self) -> bool:
        """
        Loads the image data, returns True if an image is found, False
        otherwise.
        """

        response = self.ec2.describe_images(
            Filters=[
                {
                    "Name": "name",
                    "Values": [
                        self.name,
                    ],
                },
            ],
        ).get("Images")

        if len(response) > 1:
            raise AwsException("Found more than 1 image!")

        if len(response) == 0:
            return False
        else:
            self.id = response[0].get("ImageId")
            self.state = response[0].get("State")
            self.description = response[0].get("Description")

            self.snapshot_ids = []
            for device in response[0].get("BlockDeviceMappings"):
                self.snapshot_ids.append(device.get("Ebs").get("SnapshotId"))

            return True

    def create(self, instance_id: str, description: str) -> None:
        """
        Creates an Amazon EBS-backed AMI from an Amazon EBS-backed instance that
        is either running or stopped.
        """

        if self.load() is True:
            # do not allow more images with the same name.
            raise AwsException("Image already created!")

        try:
            self.id = self.ec2.create_image(
                Description=description,
                InstanceId=instance_id,
                Name=self.name,
                NoReboot=True,
                TagSpecifications=[
                    {
                        "ResourceType": "image",
                        "Tags": [
                            {"Key": "Name", "Value": self.name},
                        ],
                    }
                ],
            ).get("ImageId")
        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the image!")

        waiter = self.ec2.get_waiter("image_available")
        waiter.wait(ImageIds=[self.id])

    def delete(self) -> None:
        """
        Deregisters the specified AMI.
        When you deregister an AMI, it doesn’t affect any instances that you’ve
        already launched from the AMI.
        All the snapshots associated with the image are deleted.
        """

        self.load()

        try:
            self.ec2.deregister_image(ImageId=self.id)

            Logger.info("Image deregistered!")

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the image!")

        try:
            for snapshot_id in self.snapshot_ids:
                self.ec2.delete_snapshot(SnapshotId=snapshot_id)

                Logger.info("Snapshot deleted!")

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the snapshots!")
