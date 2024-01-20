"""Module for the group entry processor"""
from typing import Dict, Any

import logging

from .base import EntryProcessor

from .. import CONFIG

logger: logging.Logger = logging.getLogger("ep.group")


class GroupEP(EntryProcessor):
    """Entry processor for the entry kind group."""

    def __init__(self, data: Dict[str, Any]):
        """Init."""
        super().__init__(data)
        if "group" not in data:
            logger.error("Group entry has no group: {}".format(str(data)))
            if CONFIG["main"].getboolean("strict"):
                exit(1)
            self.group: str = "<unknown>"
        else:
            self.group: str = data["group"]
        logger.debug("Group EP initialized with {}".format(self.group))

    def process(self, alias_address_provider):
        """Process."""
        logger.debug("Processing group EP with {}".format(self.group))
        from ..main import LDAP

        tuples = LDAP.get_uids_and_primary_mails_for_group(self.group)

        for uid, mail in tuples:
            if mail is None:
                logger.error("User {} does not exist or has no primary mail.".format(uid))
                if CONFIG["main"].getboolean("strict"):
                    exit(1)
            else:
                self.add_sender(uid)
                self.add_recipient(mail)
