# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2016, 2017 CERN.
#
# CERN Analysis Preservation Framework is free software; you can redistribute
# it and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Analysis Preservation Framework is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Analysis Preservation Framework; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Configuration for deposit search."""

from opensearch_dsl import Q, TermsFacet
from flask import g
from flask_login import current_user
from flask_principal import RoleNeed
from invenio_access.models import Role
from invenio_search import RecordsSearch
from invenio_search.api import DefaultFilter

from cap.modules.access.permissions import admin_permission_factory
from cap.modules.access.utils import login_required
from cap.modules.schemas.imp import get_cached_indexed_schemas_for_user_read


@login_required
def deposits_filter():
    """Filter list of deposits.

    Permit to the user to see all if:

    * The user is an admin (see
    func:`invenio_deposit.permissions:admin_permission_factory`).

    * It's called outside of a request.

    Otherwise, it filters out any deposit where user is not the owner.
    """
    if admin_permission_factory(None).can():
        return Q('term', **{'_deposit.status': 'draft'})

    roles = [
        role.id
        for role in Role.query.all()
        if RoleNeed(role) in g.identity.provides
    ]

    # we need to get the indexed schemas that the current_user
    # has read access
    schemas = get_cached_indexed_schemas_for_user_read(user_id=current_user.id)

    q = (
        Q(
            'multi_match',
            query=g.identity.id,
            fields=[
                '_access.deposit-read.users',
                '_access.deposit-admin.users',
            ],
        )
        | Q(
            'bool',
            should=[
                Q('term', **{'_collection.name': schema.name})
                for schema in schemas
            ],
        )
        | Q('terms', **{'_access.deposit-read.roles': roles})
        | Q('terms', **{'_access.deposit-admin.roles': roles})
    ) & Q('term', **{'_deposit.status': 'draft'})

    return q


class CAPDepositSearch(RecordsSearch):
    """Default search class."""

    class Meta:
        """Configuration for deposit search."""

        index = 'deposits'
        fields = ('*',)
        facets = {
            'status': TermsFacet(field='_deposit.status'),
        }
        default_filter = DefaultFilter(deposits_filter)

    def get_user_deposits(self):
        """Get draft deposits that current user owns."""
        return self.filter(
            Q('match', **{'_deposit.status': 'draft'})
            & Q(
                'multi_match', query=current_user.id, fields=['_deposit.owners']
            )
        )

    def get_collection_deposits(
        self, collection_name, collection_version=None, by_me=False
    ):
        """Get records by collection name and version."""
        q = Q('term', **{'_collection.name': collection_name})

        if by_me:
            q = q & Q(
                'multi_match', query=current_user.id, fields=['_deposit.owners']
            )
        if collection_version:
            q = q & Q('term', **{'_collection.version': collection_version})

        return self.filter(q)

    def get_shared_with_user(self):
        """Get draft deposits shared with current user ."""
        return self.filter(
            Q('match', **{'_deposit.status': 'draft'})
            & ~Q(
                'multi_match', query=current_user.id, fields=['_deposit.owners']
            )
        )

    def sort_by_latest(self):
        """Sort by latest (updated)."""
        return self.sort(
            {'_updated': {'unmapped_type': 'date', 'order': 'desc'}}
        )
