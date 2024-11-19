"""Configuration for record search."""

from opensearch_dsl import Q
from flask import g
from flask_login import current_user
from flask_principal import RoleNeed
from invenio_access.models import Role
from invenio_search import RecordsSearch
from invenio_search.api import DefaultFilter

from cap.modules.access.permissions import admin_permission_factory
from cap.modules.access.utils import login_required
from cap.modules.schemas.imp import (
    get_cached_indexed_record_schemas_for_user_read,
)


@login_required
def records_filter():
    """Filter list of deposits."""
    if admin_permission_factory(None).can():
        return Q()

    roles = [
        role.id
        for role in Role.query.all()
        if RoleNeed(role) in g.identity.provides
    ]

    # we need to get the indexed schemas that the current_user
    # has read access
    schemas = get_cached_indexed_record_schemas_for_user_read(
        user_id=current_user.id
    )
    q = (
        Q(
            'multi_match',
            query=g.identity.id,
            fields=['_access.record-read.users', '_access.record-admin.users'],
        )
        | Q(
            'bool',
            should=[
                Q('term', **{'_collection.name': schema.name})
                for schema in schemas
            ],
        )
        | Q('terms', **{'_access.record-read.roles': roles})
        | Q('terms', **{'_access.record-admin.roles': roles})
    )
    return q


class CAPRecordSearch(RecordsSearch):
    """Default search class."""

    class Meta:
        """Configuration for records search."""

        index = 'records'
        fields = ('*',)
        facets = {}
        default_filter = DefaultFilter(records_filter)

    def get_user_records(self):
        """Get records that current user owns."""
        return self.filter(
            Q('multi_match', query=current_user.id, fields=['_deposit.owners'])
        )

    def get_collection_records(
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

    def sort_by_latest(self):
        """Sort by latest (updated)."""
        return self.sort(
            {'_updated': {'unmapped_type': 'date', 'order': 'desc'}}
        )
