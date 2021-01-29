"""Module for the include alias entry processor"""
from typing import Dict, Any

import logging

from ..interface import AliasAddressProvider, AliasAddress
from .base import EntryProcessor

from .. import CONFIG

logger: logging.Logger = logging.getLogger("ep.inclu")


class IncludeAliasEP(EntryProcessor):
    """Entry processor for the entry kind include alias."""

    def __init__(self, data: Dict[str, Any]):
        """Init."""
        super().__init__()
        if "alias" not in data:
            logger.error("Include alias entry has no alias field: {}".format(str(data)))
            if CONFIG["main"].getboolean("strict"):
                exit(1)
            self.alias: str = "<unknown>"
        else:
            self.alias: str = data["alias"]
        logger.debug("Include alias EP initialized with {}".format(self.alias))

    def process(self, alias_address_provider: AliasAddressProvider):
        """Process."""
        logger.debug("Processing include alias EP with {}".format(self.alias))
        addr: AliasAddress = alias_address_provider.getAlias(self.alias)
        if addr is None:
            logger.error("Alias address given in include alias entry does not exist: {}".format(self.include))
            if CONFIG["main"].getboolean("strict"):
                exit(1)
        senders, recipients = addr.get(alias_address_provider)
        self.add_senders(senders)
        self.add_recipients(recipients)
