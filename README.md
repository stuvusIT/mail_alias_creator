# mail_alias_creator
A python program to create our mail alias tables from alias definitions

## Configuration
A configuration file is needed to configure this software.
By default it looks for `mac.conf` in the current working directory,
but this can be changed by the `-c` command line option or the `MAC_CONFIG` environment variable.

The configuration file is read by python configparser and must adhere to its format.

A typical configuration file looks like this:

```
[main]
logging_conf = logging.conf

[LDAP]
uri = ldaps://myldap.com
user_search_base = ou=users,dc=example,dc=com
group_search_base = ou=groups,dc=example,dc=com
user_filter = (objectClass=posixUser)
group_filter = (objectClass=posixGroup)
user_uid_field = uid
user_primary_mail_field = mail
group_id_field = cn
group_membership_field = memberUid
```

The `logging_conf` is file path relative to the main configuration file (or absolute). At this path should be a python `logging.conf` compatible logging configuration. This option may be omited.

In the LDAP section some more variables then shown are supported.
For a complete list and some explanations see [ldap.py](mail_alias_creator/ldap.py).

## Alias defintion format
All given files and all files (recursively) in given folders are parsed as yaml files.

Each file must be of the following format:
```yaml
meta:
  name: <name of the file>
  description: <description of the file>
aliases:
  <alias_mail>:
    description: <description of the alias>
    entries:
      - kind: <kind>
        ...
      - kind: <kind2>
        ...
  <alias_mail2> ...
  ...
```

### Alias entry kind
The following kinds of alias entries are currently supported.

#### User
The user alias kind can be used to allow users to send and receive emails to/from this alias.

Kind name: `user`

Format:
```yaml
- kind: user
  user: <username>
```

##### Optional attribues
NOT IMPLEMENTED

The following optional attributes may be added.
| name | default | description |
| ---  | --- | --- |
| `forbidSend` | `False` | Forbid the user to send via this alias.
| `forbidReceive` | `False` | Don't foward incoming mails to that user.

#### Group
The group alias kind can be used to allow a whole group to send and receive emails to/from this alias.

Kind name: `group`

Format:
```yaml
- kind: group
  group: <groupname>
```

##### Optional attribues
NOT IMPLEMENTED

The following optional attributes may be added.
| name | default | description |
| ---  | --- | --- |
| `forbidSend` | `False` | Forbid the group to send via this alias.
| `forbidReceive` | `False` | Don't foward incoming mails to the users of this group.

#### Include alias
The include alias kind can be used to include another alias in this alias.
As the argument another alias  defined in this repo must be given.
Every recipient from that given alias is also forwared incoming mails to this alias.
Every sender from that given alias send mails via this alias.
If the given address is not an alias defined in this repo there will be an error.

Kind name: `include_alias`

Format:
```yaml
- kind: include_alias
  alias: <alias address>
```

##### Optional attribues
NOT IMPLEMENTED

The following optional attributes may be added.
| name | default | description |
| ---  | --- | --- |
| `forbidSend` | `False` | Forbid the members of the given alias to send via this alias.
| `forbidReceive` | `False` | Don't foward incoming mails to the members of the given alias.

#### External address
The external address kind can be used to forward mails to external email addresses.
Sending is not possible for entries with this kind.

Kind name: `external_address`

Format:
```yaml
- kind: external_address
  address: <email address>
```
