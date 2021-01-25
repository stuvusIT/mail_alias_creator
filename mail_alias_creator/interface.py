"""Module containing some interface classes."""
from typing import Tuple, List, Dict


class AliasAddress():
    """Representation of one alias address."""

    def get(self) -> Tuple[List[str], List[str]]:
        """
        Get the senders and receivers for this alias address.

        Returns the list of senders and the list of receivers.
        """
        pass


class AliasAddressProvider():
    """A provider of alias addresses."""

    def getAlias(self, alias) -> AliasAddress:
        """
        Get the alias address object for the given alias address.

        Returns None if no alias address object with that address exists.
        """
        pass
