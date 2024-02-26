"""
Created on Mar 18, 2023

@author: vagrant
"""


class Logger(object):
    """
    classdocs
    """

    @staticmethod
    def info(message):
        print(message)

    @staticmethod
    def debug(message):
        print(f"DEBUG: {message}")

    @staticmethod
    def warn(message):
        print(f"WARN: {message}")

    @staticmethod
    def error(message):
        print(f"ERROR: {message}")
