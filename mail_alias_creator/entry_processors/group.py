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
        super().__init__()
        if "group" not in data:
            logger.error("Group entry has no group: {}".format(str(data)))
            if CONFIG["main"].getboolean("strict"):
                exit(1)
        self.group: str = data["group"]
        logger.debug("Group EP initialized with {}".format(self.group))

    def process(self, alias_address_provider):
        """Process."""
        logger.debug("Processing group EP with {}".format(self.group))
        from ..main import LDAP
        users = LDAP.get_users_in_group(self.group)
        if users == []:
            logger.warn("Group {} has no members.".format(self.group))
        mails = LDAP.get_user_primary_mails(users)
        for i, mail in enumerate(mails):
            if mail is None:
                logger.error("User {} does not exist or has no primary mail.".format(users[i]))
                if CONFIG["main"].getboolean("strict"):
                    exit(1)
            else:
                self.add_sender(users[i])
                self.add_recipient(mail)
