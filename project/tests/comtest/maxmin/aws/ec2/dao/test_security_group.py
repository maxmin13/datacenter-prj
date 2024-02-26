"""
Created on Mar 14, 2023

@author: vagrant

ec2 module tests.
"""
from _pytest.outcomes import fail
from moto import mock_ec2
import pytest

from com.maxmin.aws.ec2.dao.security_group import (
    SecurityGroup,
    CidrRule,
    SgpRule,
)
from com.maxmin.aws.exception import AwsException
from comtest.maxmin.utils import TestUtils


@pytest.fixture
def security_group():
    """
    returns a security group object to test.
    """
    return SecurityGroup("mysecgroup")


@pytest.fixture
def cidr_rule():
    """
    returns a security group rule object to test.
    """
    return CidrRule(None)


@pytest.fixture
def sgp_rule():
    """
    returns a security group rule object to test.
    """
    return SgpRule(None)


@pytest.fixture
def test_utils():
    return TestUtils()


@mock_ec2
def test_create_security_group(security_group, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")

    security_group.create("My test security group", vpc_id)

    response = test_utils.describe_security_group(security_group.id)

    assert security_group.id == response.get("GroupId")
    assert security_group.name == "mysecgroup"
    assert security_group.description is None
    assert security_group.vpc_id is None

    # verify the security group has the right tag
    tag_value = None
    for tag in response["Tags"]:
        if tag.get("Key") == "Name":
            tag_value = tag.get("Value")

    assert tag_value == "mysecgroup"

    assert response.get("GroupName") == "mysecgroup"
    assert response.get("Description") == "My test security group"
    assert response.get("VpcId") == vpc_id
    assert len(response.get("IpPermissions")) == 0
    assert len(response.get("IpPermissionsEgress")) == 1

    # verify it's the default egress rule
    assert (
        response.get("IpPermissionsEgress")[0].get("IpRanges")[0].get("CidrIp")
        == "0.0.0.0/0"
    )


@mock_ec2
def test_create_security_group_twice(security_group, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    test_utils.create_security_group(
        "mysecgroup", "My test security group", vpc_id
    )

    try:
        security_group.create("My test security group", vpc_id)

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Security group already created!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_delete_security_group(security_group, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    security_group_id = test_utils.create_security_group(
        "mysecgroup", "My test security group", vpc_id
    )

    security_group.id = security_group_id
    security_group.delete()

    response = test_utils.describe_security_groups("mysecgroup")

    assert len(response) == 0


@mock_ec2
def test_delete_not_existing_security_group(security_group):
    security_group.id = "1234"
    try:
        security_group.delete()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error deleting the security group!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_load_security_group(security_group, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    test_utils.create_security_group(
        "mysecgroup", "My test security group", vpc_id
    )

    assert security_group.load() is True

    response = test_utils.describe_security_group(security_group.id)

    assert security_group.id == response.get("GroupId")
    assert security_group.name == "mysecgroup"
    assert security_group.description == "My test security group"
    assert security_group.vpc_id == vpc_id


@mock_ec2
def test_load_security_group_not_found(security_group):
    assert security_group.load() is False


@mock_ec2
def test_allow_access_from_cidr(cidr_rule, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    security_group_id = test_utils.create_security_group(
        "mysecgroup", "My test security group", vpc_id
    )

    cidr_rule.security_group_id = security_group_id

    cidr_rule.create(80, 90, "tcp", "0.0.0.0/0", "Blackjack application")

    response = test_utils.describe_security_group(security_group_id)

    assert len(response.get("IpPermissions")) == 1
    assert response.get("IpPermissions")[0].get("FromPort") == 80
    assert response.get("IpPermissions")[0].get("ToPort") == 90
    assert response.get("IpPermissions")[0].get("IpProtocol") == "tcp"
    assert len(response.get("IpPermissions")[0].get("IpRanges")) == 1
    assert (
        response.get("IpPermissions")[0].get("IpRanges")[0].get("CidrIp")
        == "0.0.0.0/0"
    )
    assert (
        response.get("IpPermissions")[0].get("IpRanges")[0].get("Description")
        == "Blackjack application"
    )


@mock_ec2
def test_revoke_access_from_cidr(cidr_rule, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    security_group_id = test_utils.create_security_group(
        "mysecgroup", "My test security group", vpc_id
    )

    test_utils.allow_access_from_cidr(
        security_group_id,
        80,
        90,
        "tcp",
        "0.0.0.0/0",
        "My test security group",
    )

    response = test_utils.describe_security_group(security_group_id)

    assert len(response.get("IpPermissions")) == 1

    cidr_rule.security_group_id = security_group_id
    cidr_rule.delete(80, 90, "tcp", "0.0.0.0/0", "My test security group")

    response = test_utils.describe_security_group(security_group_id)

    assert len(response.get("IpPermissions")) == 0


@mock_ec2
def test_allow_access_from_security_group(sgp_rule, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    security_group_id = test_utils.create_security_group(
        "mysecgroup", "My test security group", vpc_id
    )

    # create the security group whose traffic will be authorized
    source_security_group_id = test_utils.create_security_group(
        "srcsecuritygroup", "Blackjack authorized security group", vpc_id
    )

    sgp_rule.security_group_id = security_group_id

    sgp_rule.create(
        80, 90, "tcp", source_security_group_id, "Blackjack application"
    )

    response = test_utils.describe_security_group(security_group_id)

    assert len(response.get("IpPermissions")) == 1
    assert response.get("IpPermissions")[0].get("FromPort") == 80
    assert response.get("IpPermissions")[0].get("ToPort") == 90
    assert response.get("IpPermissions")[0].get("IpProtocol") == "tcp"
    assert len(response.get("IpPermissions")[0].get("UserIdGroupPairs")) == 1
    assert (
        response.get("IpPermissions")[0]
        .get("UserIdGroupPairs")[0]
        .get("GroupId")
        == source_security_group_id
    )
    assert (
        response.get("IpPermissions")[0]
        .get("UserIdGroupPairs")[0]
        .get("Description")
        == "Blackjack application"
    )


@mock_ec2
def test_revoke_access_from_security_group(sgp_rule, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    security_group_id = test_utils.create_security_group(
        "mysecgroup", "My test security group", vpc_id
    )

    # create the security group whose traffic will be authorized
    source_security_group_id = test_utils.create_security_group(
        "srcsecuritygroup", "Blackjack authorized security group", vpc_id
    )

    sgp_rule.security_group_id = security_group_id

    test_utils.allow_access_from_security_group(
        security_group_id,
        80,
        90,
        "tcp",
        source_security_group_id,
        "My test security group",
    )

    response = test_utils.describe_security_group(security_group_id)

    assert len(response.get("IpPermissions")) == 1

    sgp_rule.delete(
        80, 90, "tcp", source_security_group_id, "My test security group"
    )

    response = test_utils.describe_security_group(security_group_id)

    assert len(response.get("IpPermissions")) == 0


@mock_ec2
def test_is_access_granted(sgp_rule, cidr_rule, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    security_group_id = test_utils.create_security_group(
        "mysecgroup", "My test security group", vpc_id
    )

    #
    # verify access is granted by cidr
    #

    cidr_rule.security_group_id = security_group_id

    response = cidr_rule.load(80, 90, "tcp", "0.0.0.0/0", "My test rule")

    assert response is False

    # authorize the traffic by cidr, add 2 rules.
    test_utils.allow_access_from_cidr(
        security_group_id,
        80,
        90,
        "tcp",
        "0.0.0.0/0",
        "My test rule 2",
    )

    test_utils.allow_access_from_cidr(
        security_group_id,
        80,
        90,
        "tcp",
        "0.0.0.0/0",
        "My test rule 1",
    )

    response = cidr_rule.load(80, 90, "tcp", "0.0.0.0/0", "My test rule")

    assert response is False

    response = cidr_rule.load(80, 90, "tcp", "1.1.1.1/1", "My test rule 1")

    assert response is False

    response = cidr_rule.load(80, 90, "tcp", "0.0.0.0/0", "My test rule 1")

    assert response is True
    assert cidr_rule.from_port == 80
    assert cidr_rule.to_port == 90
    assert cidr_rule.protocol == "tcp"
    assert cidr_rule.source_cidr == "0.0.0.0/0"
    assert cidr_rule.description == "My test rule 1"

    response = cidr_rule.load(80, 90, "tcp", "0.0.0.0/0", "My test rule 2")

    assert response is True
    assert cidr_rule.from_port == 80
    assert cidr_rule.to_port == 90
    assert cidr_rule.protocol == "tcp"
    assert cidr_rule.source_cidr == "0.0.0.0/0"
    assert cidr_rule.description == "My test rule 2"

    #
    # verify access is granted by security group
    #

    sgp_rule.security_group_id = security_group_id

    # create the security group whose traffic will be authorized
    source_security_group_id = test_utils.create_security_group(
        "srcsecuritygroup", "Blackjack authorized security group", vpc_id
    )

    response = sgp_rule.load(
        80, 90, "tcp", source_security_group_id, "My test rule 1"
    )

    assert response is False

    # authorize the traffic

    test_utils.allow_access_from_security_group(
        sgp_rule.security_group_id,
        80,
        90,
        "tcp",
        source_security_group_id,
        "My test rule 1",
    )

    response = sgp_rule.load(
        80, 90, "tcp", source_security_group_id, "My test rule"
    )

    assert response is False

    response = sgp_rule.load(80, 90, "tcp", "xxx", "My test rule 1")

    assert response is False

    response = sgp_rule.load(
        80, 90, "tcp", source_security_group_id, "My test rule 1"
    )

    assert response is True
    assert sgp_rule.from_port == 80
    assert sgp_rule.to_port == 90
    assert sgp_rule.protocol == "tcp"
    assert sgp_rule.source_security_group_id == source_security_group_id
    assert sgp_rule.description == "My test rule 1"
