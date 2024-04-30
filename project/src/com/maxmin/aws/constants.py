"""
Created on Mar 28, 2023

@author: vagrant
"""
import configparser
import os


class IniFileConstants(object):
    """
    Loads ini files into a configuration object.
    """

    def __init__(self, ini_file):
        self.config = configparser.ConfigParser()
        self.config.read(ini_file)


class Ec2Constants(IniFileConstants):
    """
    Loads the ec2.ini file
    """

    def __init__(self):
        super().__init__(ProjectFiles.EC2_CONSTANTS_FILE)

        instance = self.config["INSTANCE"]

        self.device = instance["device"]
        self.volume_size = int(instance["volume_size"])
        self.instance_type = instance["instance_type"]
        self.tenancy = instance["tenancy"]


class ProjectDirectories:
    # directory where the datacenter project is downloaded from github
    __datacenter_dir = os.getenv("DATACENTER_DIR")
    ACCESS_DIR = f"{__datacenter_dir}/access"
    CONFIG_DIR = f"{__datacenter_dir}/config"
    TEMPLATES_DIR = f"{__datacenter_dir}/project/templates"
    CONSTANTS_DIR = f"{__datacenter_dir}/project/constants"
    TEST_DIR = f"{__datacenter_dir}/project/tests"


class ProjectFiles:
    EC2_CONSTANTS_FILE = f"{ProjectDirectories.CONSTANTS_DIR}/ec2.ini"
    CLOUDINIT_TEMPLATE = f"{ProjectDirectories.TEMPLATES_DIR}/cloudinit.yml.j2"
