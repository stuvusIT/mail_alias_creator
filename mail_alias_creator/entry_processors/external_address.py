"""Module for the external address entry processor"""
from typing import Dict, Any

import logging

from .base import EntryProcessor

logger: logging.Logger = logging.getLogger("ep.eaddr")


class ExternalAddressEP(EntryProcessor):
    """Entry processor for the entry kind external address."""

    def __init__(self, data: Dict[str, Any]):
        """Init."""
        super().__init__()
        if "address" not in data:
            logger.error("External address entry has no address: {}".format(str(data)))
        self.address: str = data["address"]
        logger.debug("External Address EP initialized with {}".format(self.address))

    def process(self, alias_address_provider):
        """Process."""
        logger.debug("Processing external address EP with {}".format(self.address))
        self.add_recipient(self.address)
