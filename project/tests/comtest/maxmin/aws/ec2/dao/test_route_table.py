"""
Created on Mar 20, 2023

@author: vagrant
"""
from _pytest.outcomes import fail
from moto import mock_ec2
import pytest

from com.maxmin.aws.ec2.dao.route_table import RouteTable
from com.maxmin.aws.exception import AwsException
from comtest.maxmin.utils import TestUtils


@pytest.fixture
def route_table():
    """
    return a route table object to test.
    """
    return RouteTable("myroutetable")


@pytest.fixture
def test_utils():
    return TestUtils()


@mock_ec2
def test_create_route_table(route_table, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")

    route_table.create(vpc_id)

    response = test_utils.describe_route_table(route_table.id)

    assert route_table.id == response.get("RouteTableId")
    assert route_table.name == "myroutetable"
    assert route_table.vpc_id is None

    # verify the route table has the right tag
    tag_value = None
    for tag in response["Tags"]:
        if tag.get("Key") == "Name":
            tag_value = tag.get("Value")

    assert tag_value == "myroutetable"
    assert response.get("Routes")[0].get("State") == "active"
    assert response.get("Routes")[0].get("GatewayId") == "local"
    assert (
        response.get("Routes")[0].get("DestinationCidrBlock") == "10.0.10.0/16"
    )
    assert len(response.get("Associations")) == 0
    assert response.get("VpcId") == vpc_id


@mock_ec2
def test_create_route_table_twice(route_table, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    test_utils.create_route_table("myroutetable", vpc_id)

    try:
        route_table.create(vpc_id)

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Route table already created!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_delete_route_table(route_table, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    route_table_id = test_utils.create_route_table("myroutetable", vpc_id)
    route_table.id = route_table_id

    route_table.delete()

    response = test_utils.describe_route_tables("myroutetable")

    assert len(response) == 0


@mock_ec2
def test_delete_not_existing_route_table(route_table):
    route_table.id = "1234"
    try:
        route_table.delete()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error deleting the route table!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_load_route_table(route_table, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    route_table_id = test_utils.create_route_table("myroutetable", vpc_id)

    assert route_table.load() is True

    response = test_utils.describe_route_table(route_table_id)

    assert route_table.id == response.get("RouteTableId")
    assert route_table.name == "myroutetable"
    assert route_table.vpc_id == vpc_id

    assert len(response.get("Associations")) == 0
    assert len(response.get("Routes")) == 1
    assert (
        response.get("Routes")[0].get("DestinationCidrBlock") == "10.0.10.0/16"
    )
    assert response.get("Routes")[0].get("GatewayId") == "local"
    assert response.get("Routes")[0].get("State") == "active"
    assert response.get("VpcId") == vpc_id


@mock_ec2
def test_load_route_table_not_found(route_table):
    assert route_table.load() is False


@mock_ec2
def test_load_route_table_two_route_tables_found(route_table, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    test_utils.create_route_table("myroutetable", vpc_id)
    test_utils.create_route_table("myroutetable", vpc_id)

    try:
        route_table.load()

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Found more than 1 route table!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")


@mock_ec2
def test_route_table_has_route(route_table, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    route_table_id = test_utils.create_route_table("myroutetable", vpc_id)
    route_table.id = route_table_id
    gate_id = test_utils.create_internet_gateway("myitgate")

    test_utils.create_route(route_table_id, gate_id, "0.0.0.0/0")

    has_route = route_table.has_route(gate_id, "0.0.0.0/0")

    assert has_route is True

    has_route = route_table.has_route(gate_id, "1.1.1.1/0")

    assert has_route is False

    has_route = route_table.has_route("xxxx", "0.0.0.0/0")

    assert has_route is False


@mock_ec2
def test_create_route(route_table, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    route_table_id = test_utils.create_route_table("myroutetable", vpc_id)
    route_table.id = route_table_id
    gate_id = test_utils.create_internet_gateway("myitgate")

    route_table.create_route(gate_id, "0.0.0.0/0")

    routes = test_utils.describe_routes(route_table_id)

    created = False
    for route in routes:
        if route.get("State") == "active":
            if (
                route.get("GatewayId") == gate_id
                and route.get("DestinationCidrBlock") == "0.0.0.0/0"
            ):
                created = True
                break

    assert created is True


@mock_ec2
def test_create_route_twice(route_table, test_utils):
    vpc_id = test_utils.create_vpc("myvpc", "10.0.10.0/16")
    route_table_id = test_utils.create_route_table("myroutetable", vpc_id)
    route_table.id = route_table_id
    gate_id = test_utils.create_internet_gateway("myitgate")
    test_utils.create_route(route_table_id, gate_id, "0.0.0.0/0")

    try:
        route_table.create_route(gate_id, "0.0.0.0/0")

        fail("ERROR: an exception should have been thrown!")

    except AwsException as e:
        assert str(e) == "Error creating route!"
    except BaseException:
        fail("ERROR: an AwsException should have been raised!")
