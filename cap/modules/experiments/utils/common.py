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
"""Experiments common utils."""

from functools import wraps
from itertools import count, groupby
from os.path import join
from subprocess import CalledProcessError, check_output

import cern_sso as cern_sso_old
import cap.modules.experiments.utils.cern_sso as cern_sso_current
from cachetools.func import ttl_cache
from opensearchpy import helpers
from flask import current_app
from invenio_search.proxies import current_search_client as es


def kinit(principal, keytab):
    """Run a function with given kerberos credentials.

    Steps:
    * kinit
    * call function
    * kdestroy

    Location of keytab files defined in `cap.config.KEYTABS_LOCATION`.

    :param str principal: Kerberos principal, e.g. user@CERN.CH
    :param str keytab: Keytab filename, e.g. user.keytab
    """
    def decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            if not (principal and keytab):
                raise AssertionError('Kerberos principal and/or keytab are '
                                     'empty. Please check.')

            kt = join(current_app.config.get('KEYTABS_LOCATION'), keytab)
            try:
                check_output('kinit -kt {} {}'.format(kt, principal),
                             shell=True)
                ret_val = func(*args, **kwargs)
                return ret_val
            except CalledProcessError as err:
                current_app.logger.error(err)
                raise
            finally:
                check_output('kdestroy', shell=True)

        return wrapped_function

    return decorator


@ttl_cache(ttl=86000)  # cookie expires after 24 hours
def generate_krb_cookie_cern_sso_old(principal, kt, url):
    """Generate a HTTP cookie with given kerberos credentials.

    :param str principal: Kerberos principal, e.g. user@CERN.CH
    :param str kt: Keytab filename e.g user.keytab
    :param str url: URL

    :returns: Generated HTTP Cookie
    :rtype `requests.cookies.RequestsCookieJar`
    """
    @kinit(principal, kt)
    def generate(url):
        cookie = cern_sso_old.krb_sign_on(url)

        return cookie

    return generate(url)


@ttl_cache(ttl=86000)  # cookie expires after 24 hours
def generate_krb_cookie(principal, kt, url):
    """Generate a HTTP cookie with given kerberos credentials.

    :param str principal: Kerberos principal, e.g. user@CERN.CH
    :param str kt: Keytab filename e.g user.keytab
    :param str url: URL

    :returns: Generated HTTP Cookie
    :rtype `requests.cookies.RequestsCookieJar`
    """
    @kinit(principal, kt)
    def generate(url):
        cookie = cern_sso_current.save_sso_cookie(url, False, "auth.cern.ch")

        return cookie

    return generate(url)


def recreate_es_index_from_source(alias,
                                  source,
                                  mapping=None,
                                  settings=None,
                                  id_getter=None):
    """
    Recreate index in ES, with documents passed in source.

    As change has to be tranparent
    * put everything under index with a different name
    * redirect alias to point to newly created index
    * remove old index

    :param str alias: Alias name
    :param List(dict) source:  List of documents to index
    :param dict mapping: ES Mapping object
    :param dict settings: ES Settings object
    """
    def _batches(iterable, chunk_size=10):
        c = count()
        for _, g in groupby(iterable, lambda _: next(c) // chunk_size):
            yield g

    if es.indices.exists('{}-v1'.format(alias)):
        old_index, new_index = ('{}-v1'.format(alias), '{}-v2'.format(alias))
    else:
        old_index, new_index = ('{}-v2'.format(alias), '{}-v1'.format(alias))

    # recreate new index
    if es.indices.exists(new_index):
        es.indices.delete(index=new_index)
    es.indices.create(index=new_index,
                      body=dict(mappings=mapping, settings=settings or {}))

    print("Indexing...", end='', flush=True)

    for batch in _batches(source, chunk_size=50000):
        try:
            actions = [{
                '_id': id_getter(obj) if id_getter else None,
                '_source': obj
            } for obj in batch]
            helpers.bulk(es, actions, index=new_index)
            print('.', end='', flush=True)
        except Exception as e:
            es.indices.delete(
                index=old_index)  # delete index if sth went wrong
            raise e

    print('')

    # add newly created index under das-datasets alias
    es.indices.put_alias(index=new_index, name=alias)

    # remove old index
    if es.indices.exists(old_index):
        es.indices.delete(index=old_index)
