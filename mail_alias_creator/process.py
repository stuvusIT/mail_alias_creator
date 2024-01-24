"""Module for actually doing the processing."""
from typing import List, Tuple, Dict, Any, Optional

import logging
import yaml

from os import path, walk

from .interface import AliasAddressProvider, AliasAddress
from .entry_processors.base import EntryProcessor
from .entry_processors.external_address import ExternalAddressEP
from .entry_processors.user import UserEP
from .entry_processors.include_alias import IncludeAliasEP
from .entry_processors.group import GroupEP

from . import CONFIG

logger: logging.Logger = logging.getLogger("process")

class AliasDefinition(AliasAddress):
    """Representation of one alias definition."""

    def __init__(self, mail: str, data: Dict[str, Any]):
        self.mail: str = mail
        self.description: Optional[str] = None
        self.entries: List[EntryProcessor] = []

        self.senders: List[str] = []
        self.recipients: List[Dict[str, str]] = []
        self.has_been_processed: bool = False

        if "description" in data:
            self.description = data["description"]
        self.load_entries(data["entries"])

    def load_entries(self, entries_data: Dict[str, Any]):
        """Load the entries."""
        for entry in entries_data:
            logger.debug("For alias {}: Loading entry: {}".format(self.mail, str(entry)))
            kind: str
            if "kind" in entry:
                kind = entry["kind"]
            else:
                logger.error("Entry of alias {} has no kind: {}".format(self.mail, str(entry)))
                if CONFIG["main"].getboolean("strict"):
                    exit(1)
                return

            if kind == "external_address":
                self.entries.append(ExternalAddressEP(entry))
            elif kind == "user":
                self.entries.append(UserEP(entry))
            elif kind == "include_alias":
                self.entries.append(IncludeAliasEP(entry))
            elif kind == "group":
                self.entries.append(GroupEP(entry))
            else:
                logger.warn("Unknown entry kind in {}: {}".format(self.mail, kind))
                if CONFIG["main"].getboolean("strict"):
                    exit(1)

    def process(self, alias_address_provider: AliasAddressProvider):
        """Process."""
        logger.debug("Processing alias {}: {} entries".format(self.mail, len(self.entries)))
        for entry in self.entries:
            senders, recipients = entry.get(alias_address_provider)
            for sender in senders:
                if sender not in self.senders:
                    self.senders.append(sender)
            for recipient in recipients:
                if recipient not in self.recipients:
                    self.recipients.append(recipient)

    def get(self, alias_address_provider: AliasAddressProvider, for_final_result: bool = False) -> Tuple[List[str], List[str]]:
        """
        Get the senders and recipients represented by this alias definition.

        Returns the list of senders and the list of recipients.
        """
        logger.debug("Getting results from alias defintion for {}. Already processed: {}".format(self.mail, str(self.has_been_processed)))
        if not self.has_been_processed:
            self.process(alias_address_provider)
            self.has_been_processed = True

        senders = self.senders
        recipients = self.recipients

        if for_final_result:
            dummy_sender_uid = CONFIG["main"].get("dummy_sender_uid", "")
            if len(senders) == 0 and len(dummy_sender_uid) > 0:
                senders = [dummy_sender_uid]
            dummy_recipient_address = CONFIG["main"].get("dummy_recipient_address", "")
            if len(recipients) == 0 and len(dummy_recipient_address) > 0:
                recipients = [dummy_recipient_address]

        return senders, recipients


class Processor(AliasAddressProvider):
    """Class for processing the aliases."""

    def __init__(self):
        self.alias_definitions: Dict[str, AliasDefinition] = {}
        self.sender_aliases: List[Dict[str, str]] = []
        self.recipient_aliases: List[Dict[str, str]] = []

    def load_file(self, alias_file: str) -> List[AliasDefinition]:
        """
        Load the alias defintions from the given file.

        The given file must exist
        """
        logger.info("Getting aliases from {}".format(alias_file))
        alias_data: Dict[str, Any] = None
        with open(alias_file) as f:
            alias_data = yaml.load(f, Loader=yaml.SafeLoader)

        for mail, data in alias_data['aliases'].items():
            logger.debug("Found alias {}".format(mail))
            if mail in self.alias_definitions:
                logger.error("Found duplicate alias entry for: {}".format(mail))
                if CONFIG["main"].getboolean("strict"):
                    exit(1)

            self.alias_definitions[mail] = AliasDefinition(mail, data)

    def load_files(self, alias_files: List[str]):
        """Load the alias defintions from the given files."""
        for alias_file in alias_files:
            if path.isdir(alias_file):
                logger.debug("{} is a dir".format(alias_file))
                for root, _, files in walk(alias_file):
                    for name in files:
                        logger.debug("Found {} in dir {}".format(name, root))
                        self.load_file(path.join(root, name))
            elif path.exists(alias_file):
                logger.debug("{} is a file".format(alias_file))
                self.load_file(alias_file)
            else:
                logger.warn("The given file {} does not exist".format(alias_file))
                if CONFIG["main"].getboolean("strict"):
                    exit(1)

    def process(self):
        """Process all loaded aliases and generate the sender and receiver aliases."""
        logger.info("Start processing aliases.")
        for alias_definition in self.alias_definitions.values():
            logger.info("Proccessing {}".format(alias_definition.mail))
            senders, recipients = alias_definition.get(self, True)
            for sender in senders:
                self.sender_aliases.append({
                    "sender": sender,
                    "alias": alias_definition.mail
                })
            for recipient in recipients:
                self.recipient_aliases.append({
                    "alias": alias_definition.mail,
                    "recipient": recipient
                })

    def getAlias(self, alias) -> AliasAddress:
        """
        Get the alias address object for the given alias address.

        Returns None if no alias address object with that address exists.
        """
        if alias not in self.alias_definitions:
            logger.warn("Did not find requested alias {}".format(alias))
            return None
        return self.alias_definitions[alias]
