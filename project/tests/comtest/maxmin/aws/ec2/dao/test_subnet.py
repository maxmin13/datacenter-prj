"""
Created on Mar 14, 2023

@author: vagrant

ec2 module tests.
"""
from _pytest.outcomes import fail
from moto import mock_ec2
import pytest

from com.maxmin.aws.ec2.dao.subnet import Subnet
from com.maxmin.aws.exception import AwsException
from comtest.maxmin.utils import TestUtils


@pytest.fixture
def subnet():
    """
    return a subnet object to test.
    """
    return Subnet("mysubnet")


@pytest.fixture
def test_utils():
    return TestUtils()


@mock_ec2
def test_create_subnet(subnet, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")

    subnet.create("eu-west-1a", "10.0.10.0/24", vpc_id)

    response = test_utils.describe_subnet(subnet.id)

    assert subnet.id == response.get("SubnetId")
    assert subnet.name == "mysubnet"
    assert subnet.cidr is None
    assert subnet.az is None
    assert subnet.vpc_id is None

    # verify the subnet has the right tag
    tag_value = None
    for tag in response["Tags"]:
        if tag.get("Key") == "Name":
            tag_value = tag.get("Value")

    assert tag_value == "mysubnet"
    assert response.get("State") == "available"
    assert response.get("CidrBlock") == "10.0.10.0/24"
    assert response.get("AvailabilityZone") == "eu-west-1a"
    assert response.get("VpcId") == vpc_id


@mock_ec2
def test_create_subnet_twice(subnet, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    test_utils.create_subnet("mysubnet", "eu-west-1a", "10.0.20.0/24", vpc_id)

    try:
        subnet.create("eu-west-1a", "10.0.10.0/24", vpc_id)

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Subnet already created!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_delete_subnet(subnet, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    subnet_id = test_utils.create_subnet(
        "mysubnet", "eu-west-1a", "10.0.10.0/24", vpc_id
    )
    subnet.id = subnet_id

    subnet.delete()

    response = test_utils.describe_subnets("mysubnet")

    assert len(response) == 0


@mock_ec2
def test_delete_not_existing_subnet(subnet):
    subnet.id = "1234"
    try:
        subnet.delete()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error deleting the subnet!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_load_subnet(subnet, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    subnet_id = test_utils.create_subnet(
        "mysubnet", "eu-west-1a", "10.0.10.0/24", vpc_id
    )

    assert subnet.load() is True

    response = test_utils.describe_subnet(subnet_id)

    assert subnet.id == response.get("SubnetId")
    assert subnet.name == "mysubnet"
    assert subnet.cidr == "10.0.10.0/24"
    assert subnet.az == "eu-west-1a"
    assert subnet.vpc_id == vpc_id


@mock_ec2
def test_load_subnet_not_found(subnet):
    assert subnet.load() is False


@mock_ec2
def test_load_subnet_two_subnets_found(subnet, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    test_utils.create_subnet("mysubnet", "eu-west-1a", "10.0.10.0/24", vpc_id)
    test_utils.create_subnet("mysubnet", "eu-west-1a", "10.0.20.0/24", vpc_id)

    try:
        subnet.load()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Found more than 1 subnet!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")
