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
    DATACENTER_PROJECT_DIR = os.getenv("DATACENTER_PROJECT_DIR")
    ACCESS_DIR = f"{DATACENTER_PROJECT_DIR}/access"
    CONFIG_DIR = f"{DATACENTER_PROJECT_DIR}/config"
    TEMPLATES_DIR = f"{DATACENTER_PROJECT_DIR}/templates"


class ProjectFiles:
    EC2_CONSTANTS_FILE = f"{ProjectDirectories.CONFIG_DIR}/ec2.ini"
    CLOUDINIT_TEMPLATE = f"{ProjectDirectories.TEMPLATES_DIR}/cloudinit.yml.j2"
