"""
Created on Apr 1, 2023

@author: vagrant
"""
import os
import stat

from botocore.exceptions import ClientError

from com.maxmin.aws.client import Ec2
from com.maxmin.aws.constants import ProjectDirectories
from com.maxmin.aws.exception import AwsException
from com.maxmin.aws.logs import Logger


class Keypair(Ec2):
    """
    classdocs
    """

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.id = None
        self.public_key = None

    def load(self) -> bool:
        """
        Loads the keypair data, returns True if a keypair is found, False
        otherwise.
        """

        try:
            response = self.ec2.describe_key_pairs(
                KeyNames=[
                    self.name,
                ],
                IncludePublicKey=True,
            ).get("KeyPairs")

            self.id = response[0].get("KeyPairId")
            self.public_key = response[0].get("PublicKey")

            return True

        except ClientError as e:
            Logger.warn(str(e))
            return False

    def create(self) -> None:
        """
        Create a 2048-bit RSA key pair with the specified name.
        Amazon EC2 stores the public key and displays the private key for you
        to save to a file. The private key is returned as an unencrypted PEM
        encoded PKCS#8 private key.
        If a key with the specified name already exists, Amazon EC2 returns
        an error.
        The private key is saved in the local 'access' directory.
        """

        if self.load() is True:
            # do not allow more keypairs with the same name.
            raise AwsException("Keypair already created!")

        try:
            response = self.ec2.create_key_pair(
                KeyName=self.name,
                TagSpecifications=[
                    {
                        "ResourceType": "key-pair",
                        "Tags": [
                            {"Key": "Name", "Value": self.name},
                        ],
                    },
                ],
            )

            self.id = response.get("KeyPairId")

            private_key = response.get("KeyMaterial")
            private_key_file = f"{ProjectDirectories.ACCESS_DIR}/{self.name}"
            private_key_file_handle = open(private_key_file, "x")
            private_key_file_handle.write(private_key)
            private_key_file_handle.close()

            # Setting the given file to be read by the owner.
            os.chmod(private_key_file, stat.S_IREAD)

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error creating the keypair!")

    def delete(self) -> None:
        """
        Deletes the specified key pair, by removing the public key from Amazon
        EC2 and deleting the local private key file.
        """

        try:
            self.ec2.delete_key_pair(KeyName=self.name)

            private_key = f"{ProjectDirectories.ACCESS_DIR}/{self.name}"

            if os.path.isfile(private_key) is True:
                os.remove(private_key)

            Logger.info("Keypair deleted!")

        except Exception as e:
            Logger.error(str(e))
            raise AwsException("Error deleting the keypair!")
