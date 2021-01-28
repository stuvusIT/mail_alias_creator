"""Module for the user entry processor"""
from typing import Dict, Any

import logging

from .base import EntryProcessor

from .. import CONFIG

logger: logging.Logger = logging.getLogger("ep.user")


class UserEP(EntryProcessor):
    """Entry processor for the entry kind user."""

    def __init__(self, data: Dict[str, Any]):
        """Init."""
        super().__init__()
        if "user" not in data:
            logger.error("User entry has no user: {}".format(str(data)))
            if CONFIG["main"].getboolean("strict"):
                exit(1)
        self.user: str = data["user"]
        logger.debug("User EP initialized with {}".format(self.user))

    def process(self, alias_address_provider):
        """Process."""
        logger.debug("Processing user EP with {}".format(self.user))
        from ..main import LDAP
        mail = LDAP.get_user_primary_mails([self.user])[0]
        if mail is None:
            logger.error("User {} does not exist or has no primary mail.".format(self.user))
            if CONFIG["main"].getboolean("strict"):
                exit(1)
        else:
            self.add_sender(self.user)
            self.add_recipient(mail)
