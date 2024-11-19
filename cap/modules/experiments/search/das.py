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
"""Search classes and methods for DAS querying."""

from opensearch_dsl import Search
from invenio_search.proxies import current_search_client as es

DAS_DATASETS_ES_CONFIG = {
    'alias': 'das-datasets',
    "mappings": {
        "properties": {
            "name": {
                "type": "keyword",
                "normalizer": "lowercase_normalizer"
            }
        }
    },
    "settings": {
        "analysis": {
            "normalizer": {
                "lowercase_normalizer": {
                    "type": "custom",
                    "filter": "lowercase"
                }
            }
        }
    }
}


class DASSearch(Search):
    """ES Search class for DAS datasets."""

    class Meta:
        """Meta class."""

        index = DAS_DATASETS_ES_CONFIG['alias']
        fields = ('name', )

    def __init__(self, **kwargs):
        """Use Meta to set kwargs defaults."""
        kwargs.setdefault('index', getattr(self.Meta, 'index', None))
        kwargs.setdefault('using', es)

        super(DASSearch, self).__init__(**kwargs)

    def prefix_search(self, prefix):
        return self.query('query_string', query=prefix, default_field='name')

    def exact_search(self, term):
        return self.query('match', name=term)
