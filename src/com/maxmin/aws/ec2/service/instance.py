"""
Created on Apr 2, 2023

@author: vagrant
"""
import base64
import crypt

import jinja2

from com.maxmin.aws.constants import ProjectFiles
from com.maxmin.aws.ec2.dao.image import Image
from com.maxmin.aws.ec2.dao.instance import Instance
from com.maxmin.aws.ec2.dao.security_group import SecurityGroup
from com.maxmin.aws.ec2.dao.ssh import Keypair
from com.maxmin.aws.ec2.dao.subnet import Subnet
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class InstanceService(object):
    def create_instance(
        self,
        parent_image_nm: str,
        security_group_nm: str,
        subnet_nm: str,
        keypair_nm: str,
        private_ip: str,
        hostname: str,
        user_nm: str,
        user_pwd: str,
        tags: list,
    ) -> None:
        """
        Creates/runs an instance.
        """
        try:
            environment = jinja2.Environment()
            with open(ProjectFiles.CLOUDINIT_TEMPLATE, "r") as file:
                cloudinit_template = file.read()

            template = environment.from_string(cloudinit_template)

            salt = crypt.mksalt(method=crypt.METHOD_SHA512, rounds=4096)
            hashed_pwd = crypt.crypt(user_pwd, salt)
            keypair = Keypair(keypair_nm)
            keypair.load()

            cloudinit_data = {
                "username": user_nm,
                "hostname": hostname,
                "hashed_password": hashed_pwd,
                "public_key": keypair.public_key,
            }

            cloudinit_config = template.render(cloudinit_data)
            cloudinit_config_b64 = base64.b64encode(
                bytes(str(cloudinit_config), "utf-8")
            )

            parent_image = Image(parent_image_nm)
            
            if parent_image.load() is False:
                raise AwsException("Error loading image!")
                
            security_group = SecurityGroup(security_group_nm)
            security_group.load()
            subnet = Subnet(subnet_nm)
            subnet.load()

            instance = Instance(tags)
            if instance.load() is False:
                Logger.info("Creating instance ...")

                instance.create(
                    parent_image.id,
                    security_group.id,
                    subnet.id,
                    private_ip,
                    cloudinit_config_b64,
                    tags,
                )

                Logger.info("Instance successfully created!")

            else:
                Logger.warn("Instance already created!")

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the instance!")
