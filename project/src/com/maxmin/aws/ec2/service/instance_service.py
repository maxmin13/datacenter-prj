"""
Created on Apr 2, 2023

@author: vagrant
"""
import base64
import crypt

import jinja2

from com.maxmin.aws.constants import ProjectFiles
from com.maxmin.aws.ec2.dao.image_dao import ImageDao
from com.maxmin.aws.ec2.dao.instance_dao import InstanceDao
from com.maxmin.aws.ec2.dao.security_group_dao import SecurityGroupDao
from com.maxmin.aws.ec2.dao.ssh_dao import KeypairDao
from com.maxmin.aws.ec2.dao.subnet_dao import SubnetDao
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class InstanceService(object):
    def create_instance(
        self,
        instance_nm: str,
        parent_image_nm: str,
        security_group_nm: str,
        subnet_nm: str,
        keypair: KeypairDao,
        private_ip: str,
        user_nm: str,
        user_pwd: str,
        tags: list,
        host_name: str,
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
            keypair.load()

            cloudinit_data = {
                "username": user_nm,
                "hostname": host_name,
                "hashed_password": hashed_pwd,
                "public_key": keypair.public_key,
            }

            cloudinit_config = template.render(cloudinit_data)
            cloudinit_config_b64 = base64.b64encode(
                bytes(str(cloudinit_config), "utf-8")
            )

            parent_image_dao = ImageDao(parent_image_nm)

            if parent_image_dao.load() is False:
                raise AwsException("Error loading image!")

            security_group_dao = SecurityGroupDao(security_group_nm)
            security_group_dao.load()
            subnet_dao = SubnetDao(subnet_nm)
            subnet_dao.load()

            instance_dao = InstanceDao(instance_nm)
            if instance_dao.load() is False:
                Logger.info("Creating instance ...")

                instance_dao.create(
                    parent_image_dao.id,
                    security_group_dao.id,
                    subnet_dao.id,
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
