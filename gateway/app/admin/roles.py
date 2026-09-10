# Copyright 2017-present, The Visdom Authors
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

"""Who may see what in the admin panel.

Reading every user's data is itself a privilege, so the role decides which
models are visible rather than only which actions are allowed. Write
permissions attach to these same roles when actions are added.
"""

VIEWER = "viewer"
SUPPORT = "support"
SUPERADMIN = "superadmin"

ROLES = (VIEWER, SUPPORT, SUPERADMIN)

_VISIBLE = {
    VIEWER: {"User", "Workspace", "Membership"},
    SUPPORT: {
        "User",
        "Workspace",
        "Membership",
        "APIKey",
        "WorkspaceInvite",
        "SharedLink",
        "AdminAction",
    },
    SUPERADMIN: {
        "User",
        "Workspace",
        "Membership",
        "APIKey",
        "WorkspaceInvite",
        "SharedLink",
        "AdminUser",
        "AdminAction",
    },
}


# Changing data is a narrower privilege than reading it, so it is answered
# separately rather than implied by visibility. Support handles the day to day
# incident: revoking a leaked key, or stopping an account that is misbehaving.
# Anything that decides what someone is entitled to stays with a superadmin.
_CHANGEABLE = {
    VIEWER: set(),
    SUPPORT: {"APIKey", "User", "Workspace", "Membership"},
    SUPERADMIN: {"APIKey", "User", "Workspace", "Membership"},
}

# Removing a row is narrower again. Support can change what someone is allowed
# to do; taking their access away entirely, and the record of it with them,
# stays with a superadmin.
_REMOVABLE = {
    VIEWER: set(),
    SUPPORT: set(),
    SUPERADMIN: {"Membership"},
}

# Adding a row is narrower still, and only staff accounts can be added at all.
# Everything else in the panel is created by someone using the product, so there
# is nothing there for staff to make. Handing out console access decides who can
# read every account's data, which is a superadmin's call.
_ADDABLE = {
    VIEWER: set(),
    SUPPORT: set(),
    SUPERADMIN: {"AdminUser"},
}

# What each role may set, within a model it can change at all. Restricting the
# form is what keeps "suspend an account" from also being "edit an account".
# Suspending a workspace is reversible and leaves everything on disk, so it sits
# with the rest of support's day to day. Moving one to the trash starts a clock
# that ends in deletion, so it stays with a superadmin even though the step
# itself is just as reversible.
_EDITABLE_FIELDS = {
    SUPPORT: {
        "APIKey": {"is_active"},
        "User": {"is_active"},
        "Workspace": {"is_active"},
        "Membership": {"role"},
    },
    SUPERADMIN: {
        "APIKey": {"is_active"},
        "User": {"is_active", "tier"},
        "Workspace": {"is_active", "trashed_at"},
        "Membership": {"role"},
    },
}


def can_see(role, model_name):
    return model_name in _VISIBLE.get(role, set())


def can_change(role, model_name):
    return model_name in _CHANGEABLE.get(role, set())


def editable_fields(role, model_name):
    """The fields this role may set on this model, empty when it may not."""
    return _EDITABLE_FIELDS.get(role, {}).get(model_name, set())


def can_add(role, model_name):
    """Whether this role may create a row of this model."""
    return model_name in _ADDABLE.get(role, set())


def can_remove(role, model_name):
    """Whether this role may delete a row of this model outright."""
    return model_name in _REMOVABLE.get(role, set())


def is_valid(role):
    return role in ROLES
