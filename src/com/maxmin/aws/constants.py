"""
Created on Mar 28, 2023

@author: vagrant
"""
import configparser


class ApplicationConstants(object):
    """
    Loads ini files into a configuration object.
    """

    def __init__(self, ini_file):
        self.config = configparser.ConfigParser()
        self.config.read(ini_file)


class Ec2Constants(ApplicationConstants):
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


class Route53Constants(ApplicationConstants):
    """
    Loads the route53.ini file
    """

    def __init__(self):
        super().__init__(ProjectFiles.ROUTE53_CONSTANTS_FILE)

        instance = self.config["DNS_DOMAIN"]

        self.registered_domain = instance["registered_domain"]


class ProjectDirectories:
    PROJECT_DIR = "/home/vagrant/workspace/ansible-prj"
    ACCESS_DIR = f"{PROJECT_DIR}/access"
    CONFIG_DIR = f"{PROJECT_DIR}/config"
    TEMPLATES_DIR = f"{PROJECT_DIR}/templates"


class ProjectFiles:
    EC2_CONSTANTS_FILE = f"{ProjectDirectories.CONFIG_DIR}/ec2.ini"
    ROUTE53_CONSTANTS_FILE = f"{ProjectDirectories.CONFIG_DIR}/route53.ini"
    DEFAULT_CONFIG_FILE = (
        f"{ProjectDirectories.CONFIG_DIR}/cms_datacenter.json"
    )
    CLOUDINIT_TEMPLATE = f"{ProjectDirectories.TEMPLATES_DIR}/cloudinit.yml.j2"
