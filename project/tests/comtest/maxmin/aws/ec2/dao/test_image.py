"""
Created on Mar 28, 2023

@author: vagrant
"""
import boto3
from moto import mock_ec2
from pytest import fail
import pytest

from com.maxmin.aws.ec2.dao.image import Image
from com.maxmin.aws.exception import AwsException
from comtest.maxmin.aws.constants import AMI_ID
from comtest.maxmin.utils import TestUtils


@pytest.fixture
def image():
    """
    return an instance object to test.
    """
    return Image("myimage")


@pytest.fixture
def test_utils():
    return TestUtils()


@mock_ec2
def test_create_image(image, test_utils):
    instance_id = test_utils.create_instance("myinstance", AMI_ID)

    response = test_utils.describe_images("myimage")

    assert len(response) == 0

    image.create(instance_id, "test AMI from instance")

    response = test_utils.describe_images("myimage")

    assert len(response) == 1


@mock_ec2
def test_create_image_twice(image, test_utils):
    instance_id = test_utils.create_instance("myinstance", AMI_ID)
    test_utils.create_image("myimage", "test AMI", instance_id)

    try:
        image.create(instance_id, "test AMI")

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Image already created!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_delete_image(image, test_utils):
    instance_id = test_utils.create_instance("myinstance", AMI_ID)
    image_id = test_utils.create_image("myimage", "test AMI", instance_id)
    image.id = image_id

    response = test_utils.describe_images("myimage")

    assert len(response) == 1

    snapshot_id = (
        response[0].get("BlockDeviceMappings")[0].get("Ebs").get("SnapshotId")
    )
    response = test_utils.decribe_snapshot(snapshot_id)

    assert response.get("State") == "completed"

    image.delete()

    response = test_utils.describe_images("myimage")

    assert len(response) == 0

    try:
        response = boto3.client("ec2").describe_snapshots(
            SnapshotIds=[
                snapshot_id,
            ],
        )
        fail("ERROR: an exception should have been thrown!")
    except BaseException as e:
        assert (
            str(e)
            == "An error occurred (InvalidSnapshot.NotFound) when calling the DescribeSnapshots operation: None"
        )


@mock_ec2
def test_delete_not_existing_image(image):
    image.id = "1234"
    try:
        image.delete()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error deleting the image!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_load_image(image, test_utils):
    instance_id = test_utils.create_instance("myinstance", AMI_ID)
    image_id = test_utils.create_image("myimage", "test AMI", instance_id)
    response = test_utils.decribe_image(image_id)

    assert image.load() is True

    assert image.id == response.get("ImageId")
    assert image.description == "test AMI"
    assert image.name == "myimage"
    assert image.state == "available"
    assert len(image.snapshot_ids) == 1


@mock_ec2
def test_load_image_not_found(image):
    assert image.load() is False


@mock_ec2
def test_load_vpc_two_images_found(image, test_utils):
    instance_id = test_utils.create_instance("myinstance", AMI_ID)
    test_utils.create_image("myimage", "test AMI", instance_id)
    test_utils.create_image("myimage", "test AMI", instance_id)

    try:
        image.load()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Found more than 1 image!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")
