"""
Created on Mar 28, 2023

@author: vagrant
"""
import os
import stat

from moto import mock_ec2
from pytest import fail
import pytest

from com.maxmin.aws.constants import ProjectDirectories
from com.maxmin.aws.ec2.dao.ssh import Keypair
from com.maxmin.aws.exception import AwsException
from comtest.maxmin.utils import TestUtils

PRIVATE_KEY = f"{ProjectDirectories.ACCESS_DIR}/mykeypair"


@pytest.fixture
def keypair():
    """
    return an keypar object to test.
    """
    return Keypair("mykeypair")


@pytest.fixture
def test_utils():
    return TestUtils()


def clear():
    if os.path.isfile(PRIVATE_KEY) is True:
        os.remove(PRIVATE_KEY)


@mock_ec2
def test_create_keypair(keypair, test_utils):
    try:
        keypair.create()

        response = test_utils.decribe_keypairs("mykeypair")

        assert keypair.id == response[0].get("KeyPairId")
        assert keypair.name == "mykeypair"
        assert keypair.public_key is None

        assert os.path.isfile(PRIVATE_KEY) is True

        st = os.stat(PRIVATE_KEY)

        assert bool(st.st_mode & stat.S_IREAD) is True

    except BaseException:
        fail("create keypair test failed!")
    finally:
        clear()


@mock_ec2
def test_create_keypair_twice(keypair, test_utils):
    test_utils.create_keypair("mykeypair")

    try:
        keypair.create()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Keypair already created!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")
    finally:
        clear()


@mock_ec2
def test_delete_keypair(keypair, test_utils):
    try:
        test_utils.create_keypair("mykeypair")

        response = test_utils.decribe_keypairs("mykeypair")

        assert response[0].get("KeyName") == "mykeypair"
        assert os.path.isfile(PRIVATE_KEY) is True

        keypair.delete()

        response = test_utils.decribe_keypairs("mykeypair")

        assert len(response) == 0
        assert os.path.isfile(PRIVATE_KEY) is False

    except BaseException:
        fail("delete keypair test failed!")
    finally:
        clear()


@mock_ec2
def test_delete_not_existing_keypair(keypair):
    keypair.delete()

    # no error expected
    pass


@mock_ec2
def test_load_keypair(keypair, test_utils):
    try:
        assert keypair.load() is False

        test_utils.create_keypair("mykeypair")

        assert keypair.load() is True

        response = test_utils.decribe_keypairs("mykeypair")

        assert keypair.id == response[0].get("KeyPairId")
        assert keypair.name == "mykeypair"
        assert keypair.public_key == response[0].get("PublicKey")

    except BaseException:
        fail("load keypair test failed!")
    finally:
        clear()
