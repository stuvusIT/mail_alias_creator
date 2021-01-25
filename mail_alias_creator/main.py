#!/usr/bin/env python3
from typing import List

from os import environ, path
from json import dump

import argparse
import logging
import logging.config

from . import CONFIG
from .ldap import LDAPConnector
from .process import Processor

LDAP: LDAPConnector = None


class EnvDefault(argparse.Action):
    """Argparse action to use the env as fallback."""

    def __init__(self, envvar, required=True, default=None, **kwargs):
        if not default and envvar:
            if envvar in environ:
                default = environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


def run(config_file: str, alias_files: List[str]):
    """Process the given alias files using the given config file."""
    config_file_abs = path.abspath(config_file)
    dir_path = path.dirname(config_file_abs)
    CONFIG.read(config_file_abs)
    if "main" in CONFIG and "logging_conf" in CONFIG["main"]:
        logging_config_path = path.join(dir_path, CONFIG["main"]["logging_conf"])
        logging.config.fileConfig(logging_config_path, disable_existing_loggers=False)
    logger = logging.getLogger("main")
    logger.info("Master log level: {}".format(logging.getLevelName(logging.root.level)))

    global LDAP
    LDAP = LDAPConnector()
    processor = Processor()
    processor.load_files(alias_files)
    processor.process()
    with open("sender_aliases.json", 'w') as f:
        dump(processor.sender_aliases, f)
    with open("recipient_aliases.json", 'w') as f:
        dump(processor.recipient_aliases, f)


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Create our mail alias tables from alias definitions')
    parser.add_argument('--config', '-c', metavar='file', action=EnvDefault, envvar='MAC_CONFIG', required=False, default="./mac.conf",
                        help='The config file to use. Defaults to "./mac.conf". Can also be specified via the environment variable MAC_CONFIG')
    parser.add_argument('alias_files', nargs='+',
                        help='The alias files to be used for generation. May contain folders, which should be recursed.')

    args = parser.parse_args()
    run(args.config, args.alias_files)


if __name__ == "__main__":
    main()
