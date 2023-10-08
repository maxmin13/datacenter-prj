"""
Created on Mar 28, 2023

@author: vagrant
"""
import os

from moto import mock_ec2
from pytest import fail
import pytest

from com.maxmin.aws.constants import ProjectDirectories
from com.maxmin.aws.ec2.dao.instance import Instance
from com.maxmin.aws.ec2.dao.ssh import Keypair
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger
from comtest.maxmin.aws.constants import AMI_ID
from comtest.maxmin.utils import TestUtils

PRIVATE_KEY = f"{ProjectDirectories.ACCESS_DIR}/mykeypair"


@pytest.fixture
def instance():
    """
    return an instance object to test.
    """
    return Instance([{"Key": "Name", "Value": "guest-box"}])


@pytest.fixture
def test_utils():
    return TestUtils()


def clear():
    if os.path.isfile(PRIVATE_KEY) is True:
        os.remove(PRIVATE_KEY)


@mock_ec2
def test_create_instance(instance, test_utils):
    try:
        vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
        security_group_id = test_utils.create_security_group(
            "mysecgroup", "My test security group", vpc_id
        )
        subnet_id = test_utils.create_subnet(
            "mysubnet", "eu-west-1a", "10.0.20.0/24", vpc_id
        )

        response = test_utils.describe_instances("guest-box")

        assert len(response) == 0

        keypair_id = test_utils.create_keypair("mykeypair")
        keypair = Keypair("mykeypair")
        keypair.id = keypair_id

        tags = [
            {"Key": "Class", "Value": "webserver"},
            {"Key": "Name", "Value": "guest-box"},
        ]

        instance.create(
            AMI_ID, security_group_id, subnet_id, "10.0.20.10", "c_init", tags
        )

        response = test_utils.describe_instances("guest-box")

        assert len(response) == 1
    except BaseException as e:
        Logger.error(str(e))
        fail("Create instance test failed!")
    finally:
        clear()


@mock_ec2
def test_create_instance_twice(instance, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    security_group_id = test_utils.create_security_group(
        "mysecgroup", "My test security group", vpc_id
    )
    subnet_id = test_utils.create_subnet(
        "mysubnet", "eu-west-1a", "10.0.20.0/24", vpc_id
    )
    test_utils.create_instance("guest-box", AMI_ID)

    keypair_id = test_utils.create_keypair("mykeypair")
    keypair = Keypair("mykeypair")
    keypair.id = keypair_id

    tags = [
        {"Key": "Class", "Value": "webserver"},
        {"Key": "Name", "Value": "guest-box"},
    ]

    try:
        instance.create(
            AMI_ID, security_group_id, subnet_id, "10.0.20.10", "c_init", tags
        )

        fail("An exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Instance already created!"
    except BaseException as b:
        Logger.error(b)
        fail("An AwsException should have been raised!")
    finally:
        clear()


@mock_ec2
def test_delete_instance(instance, test_utils):
    instance_id = test_utils.create_instance("guest-box", AMI_ID)
    instance.id = instance_id

    response = test_utils.describe_instances("guest-box")

    assert response[0].get("State").get("Name") == "running"

    instance.delete()

    response = test_utils.describe_instances("guest-box")

    assert response[0].get("State").get("Name") == "terminated"


@mock_ec2
def test_delete_not_existing_instance(instance):
    instance.id = "1234"
    try:
        instance.delete()

        fail("An exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error deleting the instance!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_load_instance(instance, test_utils):
    instance_id = test_utils.create_instance("guest-box", AMI_ID)
    response = test_utils.decribe_instance(instance_id)

    assert instance.load() is True

    assert instance.id == response.get("InstanceId")

    """
    TODO
    print(instance.name)
    print(instance.id)
    print(instance.state)
    print(instance.az)
    print(instance.private_ip)
    print(instance.public_ip)
    print(instance.instance_profile)
    print(instance.security_group_id)
    print(instance.subnet_id)
    print(instance.image_id)
    print(instance.vpc_id)
    """


@mock_ec2
def test_load_instance_not_found(instance):
    assert instance.load() is False


"""
TODO
@mock_ec2
def test_stop_instance(instance, test_utils): 
"""
