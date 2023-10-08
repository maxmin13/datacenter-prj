"""
Created on Mar 20, 2023

@author: vagrant
"""

from _pytest.outcomes import fail
from moto import mock_ec2
import pytest

from com.maxmin.aws.ec2.dao.internet_gateway import InternetGateway
from com.maxmin.aws.exception import AwsException
from comtest.maxmin.utils import TestUtils


@pytest.fixture
def internet_gateway():
    """
    return an internet gateway object to test.
    """
    return InternetGateway("myitgate")


@pytest.fixture
def test_utils():
    return TestUtils()


@mock_ec2
def test_create_internet_gateway(internet_gateway, test_utils):
    internet_gateway.create()

    response = test_utils.describe_internet_gateway(internet_gateway.id)

    assert internet_gateway.id == response.get("InternetGatewayId")
    assert internet_gateway.name == "myitgate"
    assert internet_gateway.vpc_id is None

    # verify the internet gateway has the right tag
    tag_value = None
    for tag in response["Tags"]:
        if tag.get("Key") == "Name":
            tag_value = tag.get("Value")

    assert tag_value == "myitgate"
    assert len(response.get("Attachments")) == 0


@mock_ec2
def test_create_internet_gateway_twice(internet_gateway, test_utils):
    test_utils.create_internet_gateway("myitgate")

    try:
        internet_gateway.create()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Internet gateway already created!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_delete_internet_gateway(internet_gateway, test_utils):
    gate_id = test_utils.create_internet_gateway("myitgate")
    internet_gateway.id = gate_id

    internet_gateway.delete()

    response = test_utils.describe_internet_gateways("myitgate")

    assert len(response) == 0


@mock_ec2
def test_delete_not_existing_internet_gateway(internet_gateway):
    internet_gateway.id = "1234"
    try:
        internet_gateway.delete()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error deleting the Internet gateway!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_load_internet_gateway(internet_gateway, test_utils):
    gate_id = test_utils.create_internet_gateway("myitgate")

    assert internet_gateway.load() is True

    response = test_utils.describe_internet_gateway(gate_id)

    assert internet_gateway.id == response.get("InternetGatewayId")
    assert internet_gateway.name == "myitgate"
    assert internet_gateway.vpc_id is None


@mock_ec2
def test_load_internet_gateway_not_found(internet_gateway):
    assert internet_gateway.load() is False


@mock_ec2
def test_load_internet_gateway_two_internet_gateways_found(
    internet_gateway, test_utils
):
    test_utils.create_internet_gateway("myitgate")
    test_utils.create_internet_gateway("myitgate")

    try:
        internet_gateway.load()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Found more than 1 Internet gateway!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_attach_internet_gateway_to_vpc(internet_gateway, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    gate_id = test_utils.create_internet_gateway("myitgate")
    internet_gateway.id = gate_id

    internet_gateway.attach_to(vpc_id)

    response = test_utils.describe_internet_gateway(gate_id)

    assert response.get("Attachments")[0].get("State") == "available"
    assert response.get("Attachments")[0].get("VpcId") == vpc_id


@mock_ec2
def test_attach_internet_gateway_to_vpc_twice(internet_gateway, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    gate_id = test_utils.create_internet_gateway("myitgate")
    test_utils.attach_gateway_to_vpc(vpc_id, gate_id)
    internet_gateway.id = gate_id

    try:
        internet_gateway.attach_to(vpc_id)

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error attaching the Internet gateway to the vpc!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")

    response = test_utils.describe_internet_gateway(gate_id)

    assert response.get("Attachments")[0].get("State") == "available"
    assert response.get("Attachments")[0].get("VpcId") == vpc_id


@mock_ec2
def test_detach_internet_gateway_from_vpc(internet_gateway, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    gate_id = test_utils.create_internet_gateway("myitgate")
    test_utils.attach_gateway_to_vpc(vpc_id, gate_id)
    internet_gateway.id = gate_id

    internet_gateway.detach_from(vpc_id)

    response = test_utils.describe_internet_gateways("myitgate")

    assert len(response) == 1
    assert len(response[0].get("Attachments")) == 0


@mock_ec2
def test_detach_not_attached_internet_gateway_from_vpc(
    internet_gateway, test_utils
):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    gate_id = test_utils.create_internet_gateway("myitgate")
    internet_gateway.id = gate_id

    try:
        internet_gateway.detach_from(vpc_id)

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error detaching the Internet gateway to the vpc!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_load_internet_gateway_after_attaching_internet_gateways_to_vpc(
    internet_gateway, test_utils
):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    gate_id = test_utils.create_internet_gateway("myitgate")
    test_utils.attach_gateway_to_vpc(vpc_id, gate_id)

    internet_gateway.load()

    assert internet_gateway.vpc_id == vpc_id
    assert internet_gateway.id == gate_id
    assert internet_gateway.name == "myitgate"
