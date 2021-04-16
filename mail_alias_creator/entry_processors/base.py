"""Module for the base entry processor."""
from typing import List, Dict, Tuple, Any

import logging

from ..interface import AliasAddressProvider

from .. import CONFIG

logger: logging.Logger = logging.getLogger("ep.base")


class EntryProcessor():
    """Base class for every entry processor."""

    def __init__(self, data: Dict[str, Any]):
        self.senders: List[str] = []
        self.recipients: List[Dict[str, str]] = []
        self.has_been_processed: bool = False
        self.forbid_send: bool = False
        self.forbid_receive: bool = False
        if "forbidSend" in data:
            value = data["forbidSend"]
            if not isinstance(value, bool):
                logger.error("Entry has key forbidSend but value is not a boolean: {}".format(str(data)))
                if CONFIG["main"].getboolean("strict"):
                     exit(1)
                value = False
            if value:
                self.forbid_send = True
                logger.debug("This entry is forbidden to send.")
        if "forbidReceive" in data:
            value = data["forbidReceive"]
            if not isinstance(value, bool):
                logger.error("Entry has key forbidReceive but value is not a boolean: {}".format(str(data)))
                if CONFIG["main"].getboolean("strict"):
                     exit(1)
                value = False
            if value:
                self.forbid_receive = True
                logger.debug("This entry is forbidden to receive.")

    def add_sender(self, user: str):
        """Add a sender found by this entry."""
        if self.forbid_send:
            logger.debug("Not adding sender {}, because forbidSend.".format(user))
        else:
            logger.debug("Add sender {}".format(user))
            self.senders.append(user)

    def add_recipient(self, address: str):
        """Add a recipient found by this entry."""
        if self.forbid_receive:
            logger.debug("Not adding recipient {}, because forbidReceive.".format(address))
        else:
            logger.debug("Add recipient {}".format(address))
            self.recipients.append(address)

    def add_senders(self, users: List[str]):
        """Add multiple senders found by this entry."""
        if self.forbid_send:
            logger.debug("Not adding senders {}, because forbidSend.".format(str(users)))
        else:
            logger.debug("Add senders {}".format(str(users)))
            self.senders += users

    def add_recipients(self, addresses: List[str]):
        """Add multiple recipients found by this entry."""
        if self.forbid_receive:
            logger.debug("Not adding recipients {}, because forbidReceive.".format(str(addresses)))
        else:
            logger.debug("Add recipients {}".format(str(addresses)))
            self.recipients += addresses

    def process(self, alias_address_provider: AliasAddressProvider):
        """Process."""
        pass

    def get(self, alias_address_provider: AliasAddressProvider) -> Tuple[List[str], List[str]]:
        """
        Get the senders and recipients represented by the entry of this processor.

        Returns the list of senders and the list of recipients.
        """
        logger.debug("Getting results from EP. Already processed: {}".format(str(self.has_been_processed)))
        if not self.has_been_processed:
            self.process(alias_address_provider)
            self.has_been_processed = True
        return self.senders, self.recipients
