# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2016 CERN.
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
"""CAP Basic Serializers."""

from __future__ import absolute_import, print_function

from flask import current_app
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.serializers.json import JSONSerializer

from cap.modules.records.api import CAPRecord
from cap.modules.records.utils import url_to_api_url


class CAPJSONSerializer(JSONSerializer):
    """Serializer for records v1 in JSON."""

    def preprocess_search_hit(self, pid, record_hit, links_factory=None):
        """Fetch PID object for records retrievals from ES."""
        try:
            pid = PersistentIdentifier.get(
                pid_type=pid.pid_type, pid_value=pid.pid_value
            )

            result = super().preprocess_search_hit(
                pid, record_hit, links_factory=links_factory
            )
            return result
        except PIDDoesNotExistError:
            current_app.logger.info('PIDDoesNotExistError on search. Record:.')

    def serialize_search(
        self,
        pid_fetcher,
        search_result,
        links=None,
        item_links_factory=None,
        **kwargs
    ):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: OpenSearch search result.
        :param links: Dictionary of links to add to response.
        """
        links = (
            {k: url_to_api_url(v) for k, v in links.items()} if links else {}
        )

        # Get display title for "_collection" field
        collection_buckets = (
            search_result.get("aggregations", {})
            .get("facet_collection", {})
            .get("buckets", [])
        )
        if not collection_buckets:
            collection_buckets = (
                search_result.get("aggregations", {})
                .get("facet_collection", {})
                .get("filtered", {})
                .get("buckets", [])
            )

        for cb in collection_buckets:
            if "__display_name__" in cb:
                try:
                    display_name = cb["__display_name__"]["hits"]["hits"][0][
                        "_source"
                    ]["_collection"]["fullname"]
                    cb["__display_name__"] = display_name
                except Exception:
                    del cb["__display_name__"]

        return super().serialize_search(
            pid_fetcher,
            search_result,
            links=links,
            item_links_factory=item_links_factory,
        )


class RecordSerializer(CAPJSONSerializer):
    """Serializer for records v1 in JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Preprocess record serializing for to add bucket.

        Preprocess record serializing for to add bucket for fetching
        files later
        """
        result = super().preprocess_record(
            pid, record, links_factory=links_factory
        )

        # add bucket id for fetching files later
        record.__class__ = CAPRecord
        if record.files:
            result['bucket'] = record.files.bucket

        return result
