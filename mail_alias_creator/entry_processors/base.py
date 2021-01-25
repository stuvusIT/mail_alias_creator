"""Module for the base entry processor."""
from typing import List, Dict, Tuple

import logging

from ..interface import AliasAddressProvider

logger: logging.Logger = logging.getLogger("ep.base")


class EntryProcessor():
    """Base class for every entry processor."""

    def __init__(self):
        self.senders: List[str] = []
        self.recipients: List[Dict[str, str]] = []
        self.has_been_processed: bool = False

    def add_sender(self, user: str):
        """Add a sender found by this entry."""
        logger.debug("Add sender {}".format(user))
        self.senders.append(user)

    def add_recipient(self, address: str):
        """Add a recipient found by this entry."""
        logger.debug("Add recipient {}".format(address))
        self.recipients.append(address)

    def add_senders(self, users: List[str]):
        """Add multiple senders found by this entry."""
        logger.debug("Add senders {}".format(str(users)))
        self.senders += users

    def add_recipients(self, addresses: List[str]):
        """Add multiple recipients found by this entry."""
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
