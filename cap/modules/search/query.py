# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2017 CERN.
#
# CERN Open Data Portal is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Open Data Portal is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Open Data Portal; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.
"""CAP Query factory for REST API."""

from __future__ import absolute_import, print_function

from opensearch_dsl.query import Q
from flask import current_app, request
from flask_login import current_user
from invenio_records_rest.errors import InvalidQueryRESTError
from invenio_records_rest.sorter import default_sorter_factory

from .facets import cap_facets_factory

# if any of the keywords appears in a search url as a parameter,
# will get resolved to a specified query if True or ~query if False
KEYWORD_TO_QUERY = {
    'by_bot': lambda: ~Q('exists', field='created_by'),
    'by_me': lambda: Q('match', **{'created_by': current_user.id}),
}

ESCAPE_CHAR_MAP = {
    '/': r'\/',
    '+': r'\+',
    '-': r'\-',
    '^': r'\^',
}


def cap_search_factory(self, search, query_parser=None):
    """Customize Parse query using Invenio-Query-Parser.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :returns: Tuple with search instance and URL arguments.
    """
    def _default_parser(qstr=None, **kwargs):
        """Use of the Q() from opensearch_dsl."""
        def _escape_qstr(qstr):
            return ''.join((ESCAPE_CHAR_MAP.get(char, char) for char in qstr))

        query = Q('query_string',
                  query=_escape_qstr(qstr),
                  analyzer="lowercase_whitespace_analyzer",
                  analyze_wildcard=True,
                  default_operator='AND') if qstr else Q()

        # resolve keywords to queries
        for k, v in kwargs.items():
            if k in KEYWORD_TO_QUERY:
                if v == 'True':
                    query = query & KEYWORD_TO_QUERY[k]()
                elif v == 'False':
                    query = query & ~KEYWORD_TO_QUERY[k]()

        return query

    query_string = request.values.get('q')

    # parse url params to search for keywords
    query_keywords = {
        k: request.values[k]
        for k in KEYWORD_TO_QUERY.keys() if k in request.values
    }
    query_parser = query_parser or _default_parser

    try:
        search = search.query(query_parser(query_string, **query_keywords))
    except SyntaxError:
        current_app.logger.debug("Failed parsing query: {0}".format(
            request.values.get('q', '')), exc_info=True)
        raise InvalidQueryRESTError()

    search_index = search._index[0]
    search, urlkwargs = cap_facets_factory(search, search_index)
    search, sortkwargs = default_sorter_factory(search, search_index)
    for key, value in sortkwargs.items():
        urlkwargs.add(key, value)

    urlkwargs.add('q', query_string)
    return search, urlkwargs
