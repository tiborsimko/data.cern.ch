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
"""Cern Analysis Preservation utils for CADI database."""

from itertools import islice

import requests
from flask import current_app, abort
from invenio_db import db
from invenio_search import RecordsSearch
from opensearch_dsl import Q

from cap.modules.deposit.api import CAPDeposit
from cap.modules.deposit.errors import (DepositDoesNotExist,
                                        DepositValidationError)
from cap.modules.user.errors import DoesNotExistInLDAP
from cap.modules.user.utils import (get_existing_or_register_role,
                                    get_existing_or_register_user,
                                    get_user_mail_from_ldap)

from ..errors import ExternalAPIException
from ..serializers import cadi_serializer
from .common import generate_krb_cookie


def get_sso_cookie_for_cadi():
    """Get sso cookie needed to authenticate to CADI."""
    principal, kt = current_app.config['KRB_PRINCIPALS']['CADI']
    url = current_app.config['CADI_AUTH_URL']
    return generate_krb_cookie(principal, kt, url)


def synchronize_cadi_entries(limit=None):
    """Synchronize CMS analysis with CADI database.

    Updates cadi_info in existing analysis.

    If analysis with given CADI id doesn't exist yet,
    new deposit will be created.
    All members of CMS will get a r access and cms-admin egroup rw access.

    :params int limit: number of entries to update
    """
    def _cadi_deposit(cadi_id, cadi_info):
        return {
            '$ana_type': 'cms-analysis',
            'cadi_info': cadi_info,
            'general_title': cadi_info.get('name') or cadi_id,
            '_fetched_from': 'cadi',
            '_user_edited': False,
            'basic_info': {
                'cadi_id': cadi_id
            }
        }

    entries = get_all_from_cadi()

    for entry in islice(entries, limit):
        deposit = None
        cadi_info = cadi_serializer.dump(entry).data
        cadi_id = cadi_info.pop('cadi_id')

        try:  # update if cadi deposit already exists
            deposit = get_deposit_by_cadi_id(cadi_id)
            if deposit.get('cadi_info') == cadi_info:
                current_app.logger.info(f'No changes in entry {cadi_id}.')

            else:
                deposit['cadi_info'] = cadi_info
                try:
                    deposit.commit()
                except DepositValidationError:
                    current_app.logger.exception(
                        f'Error during updating cadi info in {cadi_id}.')
                    continue
                db.session.commit()

                current_app.logger.info(f'Cadi entry {cadi_id} updated.')
        except DepositDoesNotExist:
            try:
                with db.session.begin_nested():
                    deposit = CAPDeposit.create(
                        data=_cadi_deposit(cadi_id, cadi_info))

                    # give read access to members of CMS experiment
                    deposit._add_experiment_permissions(
                        'CMS',
                        ['deposit-read'],
                    )

                    # give admin access to the contact person (if in ldap)
                    owner = _get_owner_account(cadi_info['contact'])
                    if owner:
                        deposit._add_user_permissions(
                            owner,
                            [
                                'deposit-read',
                                'deposit-update',
                                'deposit-admin',
                            ],
                            db.session,
                        )

                    # give admin access to cms admin egroups
                    admin_egroups = _get_admin_egroups(wg=cadi_id[:3])
                    for role in admin_egroups:
                        deposit._add_egroup_permissions(
                            role,
                            [
                                'deposit-read',
                                'deposit-update',
                                'deposit-admin',
                            ],
                            db.session,
                        )

                    deposit.commit()

                db.session.commit()

                current_app.logger.info(f'Cadi entry {cadi_id} added.')

            except Exception:
                if deposit and deposit.id:
                    deposit.indexer.delete(deposit)

                current_app.logger.exception(f'Error during adding {cadi_id}.')


def _get_owner_account(contact):
    contact_name = contact.split(' (')[0]
    if contact_name:
        try:
            contact_mail = get_user_mail_from_ldap(contact_name)
            return get_existing_or_register_user(contact_mail)
        except DoesNotExistInLDAP:
            current_app.logger.info(f'Couldnt find {contact_name} in LDAP.')


def _get_admin_egroups(wg):
    roles = []
    for egroup in (
            current_app.config['CMS_COORDINATORS_EGROUP'],
            current_app.config['CMS_ADMIN_EGROUP'],
            current_app.config['CMS_CONVENERS_EGROUP'].format(wg=wg),
    ):
        try:
            roles.append(get_existing_or_register_role(egroup))
        except DoesNotExistInLDAP:
            current_app.logger.info(f'Couldnt find {egroup} in LDAP.')

    return roles


def get_from_cadi_by_id(cadi_id, from_validator=False):
    """Retrieve entry with given id from CADI database.

    :params str cadi_id: CADI identifier
    :returns: entry from CADI
    :rtype dict
    """
    url = current_app.config.get('CADI_GET_RECORD_URL').format(
        id=cadi_id.upper())

    cookie = get_sso_cookie_for_cadi()
    response = requests.get(url, cookies=cookie, verify=False)

    if not response.ok:
        if from_validator:
            return False
        if response.status_code == 404:
            abort(400, 'No CADI entry found')

        raise ExternalAPIException(response)

    entry = response.json()

    return entry


def get_all_from_cadi():
    """Retrieve all active entries from CADI database.

    Entries with status inactive|superseded will be skipped.

    :returns: list of CADI entries
    :rtype list of dict
    """
    url = current_app.config.get('CADI_GET_ALL_URL')

    cookie = get_sso_cookie_for_cadi()
    response = requests.get(url=url, cookies=cookie, verify=False)

    if not response.ok:
        raise ExternalAPIException(response)

    all_entries = response.json()
    all_entries = all_entries.get("_embedded", {})
    all_entries = all_entries.get("cadiLineCapInfoList", [])

    # filter out inactive or superseded entries
    entries = (entry for entry in all_entries
               if entry['status'] not in ['Inactive', 'SUPERSEDED', 'Free'])

    return entries


def get_deposit_by_cadi_id(cadi_id):
    """Return deposit with given cadi id.

    :params str cadi_id: CADI identifier

    :rtype `cap.modules.deposits.api:CAPDeposit`
    """
    rs = RecordsSearch(index='deposits-cms-analysis')

    res = rs.query(Q('match', basic_info__cadi_id=cadi_id)) \
        .execute().hits.hits

    if not res:
        raise DepositDoesNotExist
    else:
        uuid = res[0]['_id']
        deposit = CAPDeposit.get_record(uuid)

    return deposit


def get_uuids_with_same_cadi_id(cadi_id):
    """Return list with ids attached with a specific cadi_id.

    :params str cadi_id: CADI identifier
    """
    rs = RecordsSearch(index='deposits-cms-analysis')

    res = rs.query(Q('match', basic_info__cadi_id=cadi_id)) \
        .execute().hits.hits

    if not res:
        raise DepositDoesNotExist
    else:
        uuids = [
            r._source._deposit.id
            for r in res
        ]

    return uuids

# KEEP IN MIND: DUE TO API PROBLEMS, CALL TO CADI SERVER SOMETIMES FAIL
#
# def get_updated_entries_from_cadi(from_date=None, until_date=None):
#    """Get CADI lines updated since yesterday."""
#    url = current_app.config.get('CADI_GET_CHANGES_URL')
#    now = datetime.today()
#    yesterday = now - timedelta(days=1)
#
#    resp = requests.post(url=url, params={
#        'fromDate': from_date or yesterday.strftime("%d/%m/%Y"),
#        'toDate': until_date or now.strftime("%d/%m/%Y")
#    })
#
#    data = resp.json().get('data', None)
#
#    return data
