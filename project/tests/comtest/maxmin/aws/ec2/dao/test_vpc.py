"""
Created on Mar 14, 2023

@author: vagrant

ec2 module tests.
"""
from _pytest.outcomes import fail
from moto import mock_ec2
import pytest

from com.maxmin.aws.ec2.dao.vpc import Vpc
from com.maxmin.aws.exception import AwsException
from comtest.maxmin.utils import TestUtils


@pytest.fixture
def vpc():
    """
    return a vpc object to test.
    """
    return Vpc("myvpc")


@pytest.fixture
def test_utils():
    return TestUtils()


@mock_ec2
def test_create_vpc(vpc, test_utils):
    vpc.create("10.0.10.0/16")

    response = test_utils.describe_vpc(vpc.id)

    assert vpc.id == response.get("VpcId")
    assert vpc.name == "myvpc"
    assert vpc.state is None
    assert vpc.cidr is None

    # verify the vpc has the right tag
    tag_value = None
    for tag in response["Tags"]:
        if tag.get("Key") == "Name":
            tag_value = tag.get("Value")

    assert tag_value == "myvpc"
    assert response.get("State") == "available"
    assert response.get("CidrBlock") == "10.0.10.0/16"


@mock_ec2
def test_create_vpc_twice(vpc, test_utils):
    test_utils.create_vpc("myvpc", "10.0.10.0/16")

    try:
        vpc.create("10.0.10.0/16")

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Vpc already created!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_delete_vpc(vpc, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    vpc.id = vpc_id

    vpc.delete()

    response = test_utils.describe_vpcs("myvpc")

    assert len(response) == 0


@mock_ec2
def test_delete_not_existing_vpc(vpc):
    vpc.id = "1234"
    try:
        vpc.delete()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error deleting the vpc!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_load_vpc(vpc, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    response = test_utils.describe_vpc(vpc_id)

    assert vpc.load() is True

    assert vpc.id == response.get("VpcId")
    assert vpc.name == "myvpc"
    assert vpc.state == "available"
    assert vpc.cidr == "10.0.10.0/16"


@mock_ec2
def test_load_vpc_not_found(vpc):
    assert vpc.load() is False


@mock_ec2
def test_load_vpc_two_vpcs_found(vpc, test_utils):
    test_utils.create_vpc("myvpc", "10.0.10.0/16")
    test_utils.create_vpc("myvpc", "10.0.10.0/16")

    try:
        vpc.load()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Found more than 1 vpc!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")
