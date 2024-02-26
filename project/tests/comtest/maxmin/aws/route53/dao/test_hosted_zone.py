from moto.route53 import mock_route53
import pytest

from com.maxmin.aws.route53.dao.hosted_zone import HostedZone
from comtest.maxmin.utils import TestUtils


@pytest.fixture
def hosted_zone():
    """
    return an instance object to test.
    """
    return HostedZone("maxmin.it.")


@pytest.fixture
def test_utils():
    return TestUtils()


@mock_route53
def test_load_hosted_zone(hosted_zone, test_utils):
    test_utils.create_hosted_zone("maxmin.it")

    response = test_utils.describe_hosted_zones("maxmin.it.")

    assert hosted_zone.load() is True

    assert hosted_zone.id == response[0].get("Id")
