"""Module for querying the LDAP server."""
from typing import List, Dict, Optional, Tuple

import logging

from ldap3 import Connection, Server, AUTO_BIND_NO_TLS, AUTO_BIND_TLS_BEFORE_BIND, SUBTREE
from ldap3.core.exceptions import LDAPSocketOpenError, LDAPBindError

from ldap3.utils.log import set_library_log_detail_level, OFF, BASIC, EXTENDED

from . import CONFIG

logger: logging.Logger = logging.getLogger("ldap")


class LDAPConnector():
    """Class with conenction to ldap server handling the LDAP interaction."""

    server: Server = None

    def __init__(self):
        """Init this class but not connect to the server yet."""
        ldap_config = CONFIG["LDAP"]

        # The URL of the ldap server
        self.ldap_uri: str = ldap_config.get("uri")
        # The port of the ldap server. Use None for default.
        self.port: Optional[int] = ldap_config.getint("port")
        # Whether to use ssl for the connection.
        self.ssl: bool = ldap_config.getboolean("ssl", fallback=False)
        # Whether to upgrade connection with StartTLS once bound.
        self.start_tls: bool = ldap_config.getboolean("start_tls", fallback=False)
        # The user to bind to the ldap server with. Use None for anonymous bind
        self.bind_user: Optional[str] = ldap_config.get("bind_user")
        # The password for the bind user. Must be set if the bind_user is set
        self.bind_user_password: Optional[str] = ldap_config.get("bind_user_password")
        # The search base for users.
        self.user_search_base: str = ldap_config.get("user_search_base")
        # The search base for groups.
        self.group_search_base: str = ldap_config.get("group_search_base")
        # The filter for valid users.
        self.user_filter: str = ldap_config.get("user_filter")
        # The filter for valid groups.
        self.group_filter: str = ldap_config.get("group_filter")
        # The field of a user, which is the name, that is in the group_membership_field
        self.user_uid_field: str = ldap_config.get("user_uid_field")
        # The field of a user, which is the primary mail address
        self.user_primary_mail_field: str = ldap_config.get("user_primary_mail_field")
        # The field of a group, which contains the id of the group
        self.group_id_field: str = ldap_config.get("group_id_field")
        # The field of a group, which contains the username
        self.group_membership_field: str = ldap_config.get("group_membership_field")
        # Whether to use the memberof field for simpler group lookups.
        # In this case the group_membership_field is not used.
        self.use_memberof: bool = ldap_config.getboolean("use_memberof", fallback=False)

        self.server = Server(self.ldap_uri, port=self.port, use_ssl=self.ssl, connect_timeout=5)


    @classmethod
    def combine_filters(cls, filters: List[str], use_and: bool = False) -> str:
        """
        Combines the given filters with an or or optionally and and if that parameter is true
        """
        non_empty_filters = list(filter(None, filters))

        symbol = "|"

        if use_and:
            symbol = "&"

        if not non_empty_filters:
            return ""
        elif len(non_empty_filters) == 1:
            return non_empty_filters.pop()
        else:
            return "(" + symbol + ''.join(non_empty_filters) + ")"

    def get_user_primary_mails(self, users: List[str]) -> List[Tuple[str, Optional[str]]]:
        """ Get a list of tuples of uids and the primary email addresses of the users with the given uids."""
        logger.info("Getting primary mails for users {}".format(str(users)))
        filters = []
        for user in users:
            filters.append("(" + self.user_uid_field + "=" + user + ")")
        combined_filter = LDAPConnector.combine_filters(filters)
        combined_filter = LDAPConnector.combine_filters([combined_filter, self.user_filter], use_and=True)
        logger.debug("Combined Filter: {}".format(combined_filter))
        auto_bind = AUTO_BIND_NO_TLS
        if self.start_tls:
            auto_bind = AUTO_BIND_TLS_BEFORE_BIND
        result_dict: Dict[str, str] = {}
        try:
            with Connection(self.server,
                            user=self.bind_user,
                            password=self.bind_user_password,
                            auto_bind=auto_bind,
                            read_only=True) as conn:
                if conn.search(self.user_search_base,
                               combined_filter,
                               attributes=[self.user_uid_field,
                                           self.user_primary_mail_field]):
                    logger.debug("Found these entries: {}".format(str(conn.entries)))
                    for entry in conn.entries:
                        result_dict[entry[self.user_uid_field].value] = entry[self.user_primary_mail_field].value
        except LDAPSocketOpenError as error:
            logger.warn("Unable to connect to LDAP Server.")
            raise ConnectionError("Unable to connect to LDAP Server.") from error
        except LDAPBindError as error:
            logger.warn("Unable to bind to LDAP Server.")
            raise ConnectionError("Unable to bind to LDAP Server.") from error

        result: List[Tuple[str, Optional[str]]] = []

        for user in users:
            if user not in result_dict:
                logger.warn("No primary mail found for user {}".format(user))
                result.append((user,None))
            else:
                result.append((user,result_dict[user]))
        logger.debug("Result: {}".format(result))
        return result

    def get_users_in_group(self, group: str) -> List[str]:
        """ Get a list of the users in the given group."""
        logger.info("Getting members of group  {}".format(group))
        filters = [self.group_filter, "(" + self.group_id_field + "=" + group + ")"]
        combined_filter = LDAPConnector.combine_filters(filters, use_and=True)
        logger.debug("Combined Filter: {}".format(combined_filter))
        auto_bind = AUTO_BIND_NO_TLS
        if self.start_tls:
            auto_bind = AUTO_BIND_TLS_BEFORE_BIND
        results: List[str] = []
        try:
            with Connection(self.server,
                            user=self.bind_user,
                            password=self.bind_user_password,
                            auto_bind=auto_bind,
                            read_only=True) as conn:
                if conn.search(self.group_search_base,
                               combined_filter,
                               attributes=[self.group_membership_field]):
                    logger.debug("Found these entries: {}".format(str(conn.entries)))
                    for entry in conn.entries:
                        value = entry[self.group_membership_field].value
                        if type(value) is list:
                            for member in value:
                                results.append(member)
                        elif value is not None: # value is None if group is empty
                            results.append(value)
        except LDAPSocketOpenError as error:
            logger.warn("Unable to connect to LDAP Server.")
            raise ConnectionError("Unable to connect to LDAP Server.") from error
        except LDAPBindError as error:
            logger.warn("Unable to bind to LDAP Server.")
            raise ConnectionError("Unable to bind to LDAP Server.") from error

        logger.debug("Result: {}".format(results))
        return results

    def get_uids_and_primary_mails_for_group(self, group: str) -> List[Tuple[str, Optional[str]]]:
        """Get a tuple of uid and the primary email addresses for each user in the group."""
        if not self.use_memberof:
            users = self.get_users_in_group(group)
            if users == []:
                logger.warn("Group {} has no members.".format(group))
            return self.get_user_primary_mails(users)

        logger.info("Getting primary mails for users in group {}".format(group))
        logger.debug("First: Getting group DN")
        filters = [self.group_filter, "(" + self.group_id_field + "=" + group + ")"]
        combined_filter = LDAPConnector.combine_filters(filters, use_and=True)
        logger.debug("Combined Filter: {}".format(combined_filter))
        auto_bind = AUTO_BIND_NO_TLS
        if self.start_tls:
            auto_bind = AUTO_BIND_TLS_BEFORE_BIND
        try:
            with Connection(self.server,
                            user=self.bind_user,
                            password=self.bind_user_password,
                            auto_bind=auto_bind,
                            read_only=True) as conn:
                if conn.search(self.group_search_base,
                            combined_filter,
                            attributes=None):
                    if len(conn.response) != 1:
                        logger.warn("Expected to get 1 group, but got {}".format(len(conn.response)))
                    entry = conn.response[0]
                    logger.debug("Found this response: {}".format(str(entry)))
                    group_dn = entry["dn"]
                    logger.debug("Now searching members of this group")
                    combined_filter = LDAPConnector.combine_filters(["(memberof={})".format(group_dn), self.user_filter], use_and=True)
                    logger.debug("Combined Filter: {}".format(combined_filter))
                    results: List[Tuple[str, Optional[str]]] = []
                    if conn.search(self.user_search_base,
                            combined_filter,
                            attributes=[self.user_uid_field, self.user_primary_mail_field]):
                        logger.debug("Found these entries: {}".format(str(conn.entries)))
                        for entry in conn.entries:
                            results.append((entry[self.user_uid_field].value, entry[self.user_primary_mail_field].value))
                        return results
                    else:
                        logger.warn("Group {} has no members.".format(group))
                        return []
                else:
                    logger.error("Cannot find the group {}".format(group))
                    if CONFIG["main"].getboolean("strict"):
                        exit(1)
                    return []
        except LDAPSocketOpenError as error:
            logger.warn("Unable to connect to LDAP Server.")
            raise ConnectionError("Unable to connect to LDAP Server.") from error
        except LDAPBindError as error:
            logger.warn("Unable to bind to LDAP Server.")
            raise ConnectionError("Unable to bind to LDAP Server.") from error
