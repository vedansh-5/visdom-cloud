# Copyright 2017-present, The Visdom Authors
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

"""
Records what staff change through the admin panel.

sqladmin already emits an entry for every create, update and delete it performs,
so this only has to say where those entries go and who made them. Note that the
entry is written in its own transaction, after the change has committed: a crash
in between loses the record rather than the change, so this is a trail for
answering "who did that", not a ledger the data depends on.
"""

from sqladmin.audit import DBAuditBackend

from app.models import AdminAction


class StaffAuditBackend(DBAuditBackend):
    """Writes each change into `admin_actions`, attributed to the staff account."""

    def __init__(self, session_maker, session_key, email_key):
        super().__init__(session_maker)
        self.session_key = session_key
        self.email_key = email_key

    async def get_actor(self, request):
        return request.session.get(self.session_key)

    def build_row(self, entry, actor, request):
        return AdminAction(
            # Stored as text and with no foreign key, so that removing a staff
            # account leaves the trail of what it did intact and readable.
            admin_id=str(actor) if actor else None,
            # Copied rather than only referenced, so the trail still names who
            # acted after their staff account is removed.
            admin_email=request.session.get(self.email_key),
            action=entry.action,
            model=entry.identity,
            row_id=str(entry.pk) if entry.pk is not None else None,
            changes=_serialisable(entry.changes),
            created_at=entry.timestamp,
        )


# Fields whose value must never reach the trail. The staff creation form writes
# the password through a field named for the column it lands in, so the value
# arriving here is the plaintext one. A record of who added an account is worth
# keeping; a record of the password they chose is a second place to steal it
# from, and one that outlives the account.
_SECRET_FIELDS = ("password", "password_hash", "hashed_key", "token", "secret")

_REDACTED = "[redacted]"


def _is_secret(key):
    return any(marker in key.lower() for marker in _SECRET_FIELDS)


def _serialisable(changes):
    """Coerce submitted values into something the JSON column will take.

    Form values arrive as whatever the field produced, including UUIDs, dates
    and model instances, none of which the driver can encode. Secrets are
    replaced rather than encoded, so the trail says a password was set without
    saying what it was.
    """
    if not changes:
        return None
    clean = {}
    for key, value in changes.items():
        if _is_secret(key):
            clean[key] = _REDACTED
        elif isinstance(value, (str, int, float, bool)) or value is None:
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean
