#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Cli module contains entry points to the connector.
Each method provides a way to make an interaction
between Elastic Enterprise Search and remote system
"""

import getpass
import os
from argparse import ArgumentParser

from .bootstrap_command import BootstrapCommand
from .full_sync_command import FullSyncCommand

CMD_BOOTSTRAP = "bootstrap"
CMD_FULL_SYNC = "full-sync"

commands = {
    CMD_BOOTSTRAP: BootstrapCommand,
    CMD_FULL_SYNC: FullSyncCommand,
}


def _parser():
    """Get a configured parser for the module.

    This method will initialize argument parser with a list
    of avaliable commands and their options."""
    parser = ArgumentParser(prog="ees_microsoft_outlook")
    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        metavar="CONFIGURATION_FILE_PATH",
        help="path to the configuration file",
    )
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True
    bootstrap = subparsers.add_parser(CMD_BOOTSTRAP)
    bootstrap.add_argument(
        "-n",
        "--name",
        required=True,
        type=str,
        metavar="CONTENT_SOURCE_NAME",
        help="Name of the content source to be created",
    )
    bootstrap.add_argument(
        "-u",
        "--user",
        required=False,
        type=str,
        metavar="ENTERPRISE_SEARCH_ADMIN_USER_NAME",
        help="Username of the Workplace Search admin account",
    )

    subparsers.add_parser(CMD_FULL_SYNC)
    return parser


def main(args=None):
    """Entry point for the connector."""
    if args is None:
        parser = _parser()
        args = parser.parse_args()

    if args.cmd == CMD_BOOTSTRAP and args.user:
        args.password = getpass.getpass(prompt="Password: ", stream=None)

    if not args.config_file:
        args.config_file = os.path.join(
            os.path.expanduser("~"),
            ".local",
            "config",
            "microsoft_outlook_connector.yml",
        )

    run(args)


def run(args):
    """Run the command from the parsed args.

    This method takes already parsed and validated arguments
    and attempts to run the command with specified arguments."""
    commands[args.cmd](args).execute()

    return 0
