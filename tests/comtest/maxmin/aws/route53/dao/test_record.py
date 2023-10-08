from moto.route53 import mock_route53
import pytest

from com.maxmin.aws.route53.dao.record import Record
from comtest.maxmin.utils import TestUtils


@pytest.fixture
def test_utils():
    return TestUtils()


@mock_route53
def test_load_record(test_utils):
    hosted_zone_id = test_utils.create_hosted_zone("maxmin.it")
    record = Record("com.maxmin.it", hosted_zone_id)

    assert record.load() is False

    test_utils.create_record("com.maxmin.it", "10.0.10.10", hosted_zone_id)

    assert record.load() is True

    response = test_utils.describe_records("com.maxmin.it", hosted_zone_id)

    assert record.type == response[0].get("Type")
    assert record.ip_address == response[0].get("ResourceRecords")[0].get(
        "Value"
    )


@mock_route53
def test_create_record(test_utils):
    hosted_zone_id = test_utils.create_hosted_zone("maxmin.it")
    response = test_utils.describe_records("com.maxmin.it", hosted_zone_id)

    assert len(response) == 0

    record = Record("com.maxmin.it", hosted_zone_id)
    record.create("10.0.10.10")

    response = test_utils.describe_records("com.maxmin.it", hosted_zone_id)

    assert len(response) == 1


@mock_route53
def test_delete_record(test_utils):
    hosted_zone_id = test_utils.create_hosted_zone("maxmin.it")
    test_utils.create_record("com.maxmin.it", "10.0.10.10", hosted_zone_id)

    response = test_utils.describe_records("com.maxmin.it", hosted_zone_id)

    assert len(response) == 1

    record = Record("com.maxmin.it", hosted_zone_id)
    record.delete("10.0.10.10")

    response = test_utils.describe_records("com.maxmin.it", hosted_zone_id)

    assert len(response) == 0
